from extensions.module_result.models.module_config import ModuleConfig, RagThreshold
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_oxford_knee import (
    OxfordKneeScore,
    LegAffected,
    LegData,
)
from extensions.module_result.modules.module import Module


class OxfordKneeScoreQuestionnaireModule(Module):
    moduleId = "OxfordKneeScore"
    primitives = [OxfordKneeScore]
    ragEnabled = True

    def calculate(self, primitive: OxfordKneeScore):
        legs_data = primitive.legsData

        if primitive.legAffected == LegAffected.BOTH.value:
            self._validate_if_both_legs_present(legs_data)

            self._process_right_leg_data(primitive, legs_data[0])
            self._process_left_leg_data(primitive, legs_data[1])
        else:
            if primitive.legAffected == LegAffected.RIGHT.value:
                self._process_right_leg_data(primitive, legs_data[0])
            else:
                self._process_left_leg_data(primitive, legs_data[0])

    def validate_config_body(self, module_config: ModuleConfig):
        pass

    def _process_right_leg_data(self, primitive: OxfordKneeScore, leg_data: LegData):
        leg_score = self._calculate_leg_score(leg_data)
        primitive.rightKneeScore = leg_score
        self._process_leg_data(leg_data, LegAffected.RIGHT, leg_score)

    def _process_left_leg_data(self, primitive: OxfordKneeScore, leg_data: LegData):
        leg_score = self._calculate_leg_score(leg_data)
        primitive.leftKneeScore = leg_score
        self._process_leg_data(leg_data, LegAffected.LEFT, leg_score)

    @staticmethod
    def _process_leg_data(leg_data: LegData, leg_effected: LegAffected, score: int):
        leg_data.score = score
        leg_data.legAffected = leg_effected

    @staticmethod
    def _validate_if_both_legs_present(legs_data: list[LegData]):
        if len(legs_data) != 2:
            raise Exception("Missing data for both legs")

    def _calculate_leg_score(self, leg_data: LegData) -> int:
        leg_dict = leg_data.to_dict()
        answer_scores = self._map_answers_with_scores(leg_dict.values())
        return sum(answer_scores)

    @staticmethod
    def _map_answers_with_scores(answers: list[int]) -> list[int]:
        score_mapping = {1: 4, 2: 3, 3: 2, 4: 1, 5: 0}
        return [score_mapping.get(v, 0) for v in answers]

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:

        thresholds = super(OxfordKneeScoreQuestionnaireModule, self).get_threshold_data(
            target_primitive, module_config, primitives
        )

        severities = [
            primitive[RagThreshold.SEVERITY]
            for name, primitive in thresholds.items()
            if name
            in [OxfordKneeScore.LEFT_KNEE_SCORE, OxfordKneeScore.RIGHT_KNEE_SCORE]
            if RagThreshold.SEVERITY in primitive
        ]
        if severities:
            thresholds.update({"severities": severities})

        return thresholds
