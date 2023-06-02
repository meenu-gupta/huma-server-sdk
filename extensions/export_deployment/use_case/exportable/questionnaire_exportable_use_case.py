import re
from collections import defaultdict

from tomlkit._utils import merge_dicts

from extensions.deployment.models.deployment import (
    ModuleConfig,
)
from extensions.export_deployment.helpers.convertion_helpers import (
    flat_questionnaire,
    get_primitive_dict,
    get_object_fields,
    ExportData,
    build_module_config_versions,
    replace_answer_text_with_short_codes,
)
from extensions.export_deployment.use_case.exportable.exportable_request_objects import (
    ExportableResponseObject,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)
from extensions.module_result.models.primitives import (
    Primitive,
    QuestionnaireAnswer,
    Questionnaire,
)
from extensions.module_result.modules.questionnaire import QuestionnaireModule


class QuestionnaireExportableResponseObject(ExportableResponseObject):
    def preprocess_csv_data(self, items: dict):
        for module, primitives in items.items():
            for item in primitives:
                for field_name in list(item):
                    # to keep the order and backward compatibility with tests
                    value = item.pop(field_name)
                    if field_name == Questionnaire.ANSWERS:
                        for answer in value:
                            # saving value to corresponding index in row
                            if QuestionnaireAnswer.ANSWER_TEXT in answer:
                                item[answer[QuestionnaireAnswer.QUESTION]] = answer[
                                    QuestionnaireAnswer.ANSWER_TEXT
                                ]
                            else:
                                for answer_option in answer["answerChoices"]:
                                    item[answer_option["text"]] = answer_option[
                                        "selected"
                                    ]
                        continue
                    item[field_name] = value

        super(QuestionnaireExportableResponseObject, self).preprocess_csv_data(items)


class QuestionnaireModuleExportableUseCase(ExportableUseCase):
    @classmethod
    def get_response_object(cls, data):
        return QuestionnaireExportableResponseObject(data)

    def get_raw_result(self) -> ExportData:
        modules = self.get_modules(
            self.request_object.moduleNames,
            self.request_object.excludedModuleNames,
            parent_module=QuestionnaireModule,
        )
        if not modules:
            return {}

        raw_results = self.get_module_results(
            self.request_object,
            modules,
        )

        final_results = defaultdict(list)

        for module_name, primitives in raw_results.items():
            for primitive in primitives:
                primitive_dict = get_primitive_dict(primitive)
                object_fields = get_object_fields(primitive)
                self.process_binaries(
                    primitive_dict, self.request_object, object_fields, []
                )

                if len(primitive_dict) == 0:
                    break

                questionnaire_name = module_name

                if self.request_object.questionnairePerName:
                    questionnaire_name = primitive_dict.get(
                        Questionnaire.QUESTIONNAIRE_NAME, questionnaire_name
                    )
                module_config = self.get_module_config(
                    primitive, self.request_object.moduleConfigVersions
                )

                if self.request_object.preferShortCode:
                    replace_answer_text_with_short_codes(
                        primitive_dict.get(Questionnaire.ANSWERS), module_config
                    )

                if self.request_object.splitMultipleChoice:
                    self._split_answers(primitive_dict, module_config)

                if self.request_object.useFlatStructure:
                    config_body = module_config.configBody if module_config else {}
                    merge_dicts(
                        primitive_dict,
                        flat_questionnaire(
                            config_body,
                            primitive_dict.pop("answers"),
                            self.request_object.extraQuestionIds,
                        ),
                    )

                final_results[questionnaire_name].append(primitive_dict)

        return final_results

    @staticmethod
    def _split_answers(primitive_dict: dict, module_config: ModuleConfig):
        answers = primitive_dict.get(Questionnaire.ANSWERS)
        if not module_config or not answers:
            return answers
        questions = {
            q["items"][0]["id"]: q["items"][0]
            for q in module_config.configBody["pages"]
            if q["type"] == "QUESTION" and q["items"][0]["format"] == "TEXTCHOICE"
        }
        new_answers = []
        for answer in answers:
            question = questions.get(answer[QuestionnaireAnswer.QUESTION_ID])
            if not question:
                new_answers.append(answer)
                continue

            options = question.get("options")
            answer_text = answer.pop(QuestionnaireAnswer.ANSWER_TEXT)

            selected_answers = [answer_text]
            if question.get("selectionCriteria") == "MULTIPLE":
                selected_answers = re.split(r",(?![ ])", answer_text)

            answer["answerChoices"] = []
            for option in options:
                selected = option["label"] in selected_answers
                answer["answerChoices"].append(
                    {"text": option["label"], "selected": selected}
                )
            new_answers.append(answer)
        primitive_dict[Questionnaire.ANSWERS] = new_answers

    def _get_module_config(self, module_configs_versions: dict, primitive: Primitive):
        module_versions = module_configs_versions.get(primitive.moduleId, {})
        versions = module_versions.get(primitive.moduleConfigId, {})
        if primitive.__class__ == Questionnaire:
            versions = module_versions.get(primitive.questionnaireId, {})
        module_config = versions.get(primitive.version)
        if primitive.version == 0 and not module_config:
            module_config = versions.get(None)
        return module_config

    def get_module_config_from_revision(self, primitive: Primitive):
        if primitive.__class__ == Questionnaire:
            revision = self._deployment_repo.retrieve_deployment_revision_by_module_config_version(
                deployment_id=primitive.deploymentId,
                module_id=primitive.moduleId,
                config_body_id=primitive.questionnaireId,
                module_config_version=primitive.version,
            )
        else:
            revision = self._deployment_repo.retrieve_deployment_revision_by_module_config_version(
                deployment_id=primitive.deploymentId,
                module_id=primitive.moduleId,
                module_config_id=primitive.moduleConfigId,
                module_config_version=primitive.version,
            )
        if not revision:
            return
        build_module_config_versions(
            self.request_object.moduleConfigVersions, revision.snap.moduleConfigs
        )
        return self._get_module_config(
            self.request_object.moduleConfigVersions, primitive
        )
