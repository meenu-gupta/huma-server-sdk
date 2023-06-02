import unittest
from unittest.mock import MagicMock, patch

from extensions.authorization.models.user import UnseenFlags
from extensions.common.sort import SortField
from extensions.module_result.models.primitives import Questionnaire, Primitive
from extensions.module_result.module_result_utils import AggregateFunc, AggregateMode
from extensions.module_result.modules import QuestionnaireModule
from extensions.module_result.modules.module import Module
from extensions.module_result.router.module_result_requests import (
    RetrieveUnseenModuleResultRequestObject,
)
from extensions.module_result.service.module_result_service import ModuleResultService
from sdk.common.constants import VALUE_IN
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig

PATH = "extensions.module_result.service.module_result_service"
SAMPLE_ID = "6177a6cc104c5cbb23728f40"


class PrimitiveMock(MagicMock):
    moduleResultId = SAMPLE_ID
    moduleConfigId = "some_id"
    class_name = "class_name"
    flags = {
        UnseenFlags.RED: 0,
        UnseenFlags.AMBER: 0,
        UnseenFlags.GRAY: 0,
    }


class ConfigMock:
    instance = MagicMock()
    id = "some_id"


class DeploymentMock:
    instance = MagicMock()
    moduleConfigs = [ConfigMock()]


class RequestObjectMock:
    instance = MagicMock()
    primitives = [PrimitiveMock()]
    deployment = DeploymentMock()
    module = MagicMock()
    user = MagicMock()
    moduleConfigId = "6177a6cc104c5cbb23728f40"


class ModuleResultServiceTestCase(unittest.TestCase):
    @patch(f"{PATH}.DeploymentService")
    def setUp(self, deployment_service) -> None:
        self.repo = MagicMock()
        self.service = ModuleResultService(self.repo)
        self.deployment_service = deployment_service

        def configure_with_binder(binder: inject.Binder):
            binder.bind(PhoenixServerConfig, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)
        RequestObjectMock.module.apply_overall_flags_logic.reset_mock()

    @staticmethod
    def unseen_flags(red, amber, gray):
        return {
            UnseenFlags.RED: red,
            UnseenFlags.AMBER: amber,
            UnseenFlags.GRAY: gray,
        }

    @patch(f"{PATH}.AuthorizationService")
    @patch(f"{PATH}.ModuleResultService.create_primitive")
    @patch(f"{PATH}.ModuleResultService._post_batch_create_event")
    @patch(f"{PATH}.ModuleResultService.update_unseen_flags")
    def test_success_create_module_result(
        self,
        update_unseen_flags,
        _post_batch_create_event,
        create_primitive,
        auth_service,
    ):
        req_obj = RequestObjectMock()
        req_obj.module.calculate_rag_flags.return_value = (dict(), PrimitiveMock.flags)
        self.service.create_module_result(req_obj)
        req_obj.module.preprocess.assert_called_with(req_obj.primitives, req_obj.user)
        auth_service().retrieve_user_profile.assert_called_with(req_obj.user.id)
        create_primitive.assert_called_with(
            req_obj.primitives[0], req_obj.module, save_unseen=True
        )
        _post_batch_create_event.assert_called_with(req_obj.primitives)
        update_unseen_flags.assert_called_with(req_obj.user.id)

    @patch(f"{PATH}.AuthorizationService")
    @patch(f"{PATH}.ModuleResultService.create_primitive")
    @patch(f"{PATH}.ModuleResultService._post_batch_create_event")
    @patch(f"{PATH}.ModuleResultService.update_unseen_flags")
    def test_success_create_module_result_with_primitives_flag_is_none(
        self,
        update_unseen_flags,
        _post_batch_create_event,
        create_primitive,
        auth_service,
    ):
        req_obj = RequestObjectMock()
        req_obj.primitives.append(PrimitiveMock())
        flags = PrimitiveMock.flags
        flags[UnseenFlags.GRAY] = 3

        def rag_flags_side_effect(*args, **kwargs):
            values = [
                (dict(), None),
                (dict(), None),
            ]
            for p, v in zip(req_obj.primitives, values):
                if args[0] == p:
                    return v

        req_obj.module.calculate_rag_flags.side_effect = rag_flags_side_effect
        self.service.create_module_result(req_obj)
        req_obj.module.preprocess.assert_called_with(req_obj.primitives, req_obj.user)
        auth_service().retrieve_user_profile.assert_called_with(req_obj.user.id)
        create_primitive.assert_called_with(
            req_obj.primitives[1], req_obj.module, save_unseen=True
        )
        self.assertIsNone(req_obj.primitives[0].flags)
        self.assertIsNone(req_obj.primitives[1].flags)
        update_unseen_flags.assert_called_with(req_obj.user.id)

    @patch(f"{PATH}.AuthorizationService")
    @patch(f"{PATH}.ModuleResultService.create_primitive")
    @patch(f"{PATH}.ModuleResultService._post_batch_create_event")
    @patch(f"{PATH}.ModuleResultService.update_unseen_flags")
    def test_success_create_module_result_with_two_non_rag_primitives(
        self,
        update_unseen_flags,
        _post_batch_create_event,
        create_primitive,
        auth_service,
    ):
        req_obj = RequestObjectMock()
        req_obj.primitives.append(PrimitiveMock())

        req_obj.module.calculate_rag_flags.return_value = (
            dict(),
            self.unseen_flags(0, 0, 1),
        )
        self.service.create_module_result(req_obj)
        req_obj.module.preprocess.assert_called_with(req_obj.primitives, req_obj.user)
        auth_service().retrieve_user_profile.assert_called_with(req_obj.user.id)
        create_primitive.assert_called_with(
            req_obj.primitives[1], req_obj.module, save_unseen=True
        )
        _post_batch_create_event.assert_called_with(req_obj.primitives[:2])
        call_count = req_obj.module.apply_overall_flags_logic.call_count
        self.assertEqual(len(req_obj.primitives), call_count)
        update_unseen_flags.assert_called_with(req_obj.user.id)

    @patch(f"{PATH}.AuthorizationService")
    @patch(f"{PATH}.ModuleResultService.create_primitive")
    @patch(f"{PATH}.ModuleResultService._post_batch_create_event")
    @patch(f"{PATH}.ModuleResultService.update_unseen_flags")
    def test_success_create_module_result_event_ignore_error_primitive(
        self,
        update_unseen_flags,
        _post_batch_create_event,
        create_primitive,
        auth_service,
    ):
        req_obj = RequestObjectMock()
        req_obj.primitives.append(PrimitiveMock())
        req_obj.module.calculate_rag_flags.return_value = (dict(), PrimitiveMock.flags)
        create_primitive.side_effect = ["some_id", Exception()]
        self.service.create_module_result(req_obj)
        req_obj.module.preprocess.assert_called_with(req_obj.primitives, req_obj.user)
        auth_service().retrieve_user_profile.assert_called_with(req_obj.user.id)
        create_primitive.assert_called_with(
            req_obj.primitives[1], req_obj.module, save_unseen=True
        )
        _post_batch_create_event.assert_called_with([req_obj.primitives[0]])
        update_unseen_flags.assert_called_with(req_obj.user.id)

    def test_apply_overall_flags_logic(self):
        primitives = [
            PrimitiveMock(flags=self.unseen_flags(3, 2, 11)),
            PrimitiveMock(flags=self.unseen_flags(0, 0, 2)),
            PrimitiveMock(flags=self.unseen_flags(1, 3, 2)),
        ]
        Module.apply_overall_flags_logic(primitives)
        self.assertEqual(1, primitives[0].flags[UnseenFlags.RED])
        self.assertEqual(1, sum(primitives[0].flags.values()))
        self.assertEqual(0, sum(primitives[1].flags.values()))
        self.assertEqual(0, sum(primitives[2].flags.values()))

    def test_apply_gray_flags_logic(self):
        primitives = [
            PrimitiveMock(flags=self.unseen_flags(0, 0, 1)),
            PrimitiveMock(flags=self.unseen_flags(0, 0, 3)),
        ]
        Module.apply_overall_flags_logic(primitives)
        self.assertEqual(1, primitives[0].flags[UnseenFlags.GRAY])
        self.assertEqual(1, sum(primitives[0].flags.values()))
        self.assertEqual(0, sum(primitives[1].flags.values()))

    def test_apply_flags_logic_for_grays(self):
        primitives = [
            PrimitiveMock(flags=self.unseen_flags(0, 0, 5)),
            PrimitiveMock(flags=self.unseen_flags(0, 0, 10)),
        ]
        Module.apply_overall_flags_logic(primitives)
        self.assertEqual(1, primitives[0].flags[UnseenFlags.GRAY])
        self.assertEqual(
            1, sum(primitives[0].flags.values()) + sum(primitives[1].flags.values())
        )

    @patch(f"{PATH}.ModuleResultService._create_primitive")
    @patch(f"{PATH}.ModuleResultService._pre_create")
    def test_create_primitive(self, _pre_create, _create_primitive):
        primitive = module = MagicMock()
        self.service._calculate_primitive_with_flags(primitive, module)
        self.service.create_primitive(primitive, module)
        module.calculate.assert_called_with(primitive)
        _pre_create.assert_called_with(primitive)
        _create_primitive.assert_called_with(primitive, save_unseen=False)

    @patch(f"{PATH}.report_exception", MagicMock())
    def test_check_existing_trigger_primitive(self):
        primitive = MagicMock()
        self.service._check_existing_trigger_primitive(primitive)
        self.repo.retrieve_primitive_by_name.assert_called_with(
            user_id=primitive.userId, primitive_name=primitive.moduleId
        )

    @patch(f"{PATH}.ModuleResultService._post_create")
    def test__create_primitive(self, _post_create):
        primitive = MagicMock()
        self.service._create_primitive(primitive)
        _post_create.assert_called_with(primitive)
        self.repo.create_primitive.assert_called_with(primitive, False)

    def test_retrieve_module_results(self):
        user_id = module_id = deployment_id = SAMPLE_ID
        skip = limit = 0
        direction = SortField.Direction.ASC.value
        from_date_time = to_date_time = MagicMock()
        filters = {}
        role = "some_role"
        module = MagicMock
        primitive = MagicMock()
        primitive.__name__ = "some_name"
        module.primitives = [primitive]
        self.deployment_service.retrieve_module.return_value = module
        self.service.retrieve_module_results(
            user_id,
            module_id,
            skip,
            limit,
            direction,
            from_date_time,
            to_date_time,
            filters,
            deployment_id,
            role,
        )
        self.deployment_service().retrieve_module.assert_called_with(module_id)
        self.deployment_service().retrieve_deployment.assert_called_with(deployment_id)
        self.repo.retrieve_primitives.assert_called_with(
            user_id=user_id,
            module_id=module_id,
            skip=skip,
            limit=limit,
            direction=direction,
            from_date_time=from_date_time,
            to_date_time=to_date_time,
            field_filter=filters,
            excluded_fields=None,
            module_config_id=None,
            primitive_name=primitive.__name__,
            exclude_module_ids=None,
            only_unseen_results=None,
        )

    def test_retrieve_aggregated_results(self):
        primitive_name = "some_name"
        aggregation_function = AggregateFunc.AVG.value
        mode = AggregateMode.DAILY.value
        self.service.retrieve_aggregated_results(
            primitive_name, aggregation_function, mode
        )
        self.repo.retrieve_aggregated_results.assert_called_with(
            primitive_name,
            aggregation_function,
            mode,
            None,
            None,
            None,
            None,
            None,
            None,
        )

    @patch(f"{PATH}.UpdateUserStatsEvent")
    @patch(f"{PATH}.inject")
    def test__post_batch_create_event(self, inject, stats_event):
        event_bus = MagicMock()
        inject.instance.return_value = event_bus
        primitive = MagicMock()
        primitives = [primitive]
        self.service._post_batch_create_event(primitives)
        event_bus.emit.assert_called_with(stats_event())

    @patch(f"{PATH}.AuthorizedUser")
    @patch(f"{PATH}.AuthorizationService")
    def test__trigger_key_actions(self, auth_service, authz_user):
        primitive = module = MagicMock()
        self.service._trigger_key_actions(primitive, module)
        self.deployment_service().retrieve_deployment_config.assert_called_with(
            authz_user()
        )
        module.trigger_key_actions.assert_called_with(
            user=auth_service().retrieve_user_profile(),
            key_actions=self.deployment_service()
            .retrieve_deployment_config()
            .keyActions,
            primitive=primitive,
            config_body=None,
            deployment_id=self.deployment_service().retrieve_deployment_config().id,
            start_date=None,
            group_category=None,
        )

    @patch(f"{PATH}.PostCreatePrimitiveEvent")
    @patch(f"{PATH}.inject")
    def test__post_create(self, inject, event):
        event_bus = primitive = MagicMock()
        inject.instance.return_value = event_bus
        self.service._post_create(primitive)
        event_bus.emit.assert_called_with(event.from_primitive())

    @patch(f"{PATH}.PreCreatePrimitiveEvent")
    @patch(f"{PATH}.inject")
    def test__pre_create(self, inject, event):
        event_bus = primitive = MagicMock()
        inject.instance.return_value = event_bus
        self.service._pre_create(primitive)
        event_bus.emit.assert_called_with(event.from_primitive(), raise_error=True)

    @patch(f"{PATH}.AuthorizationService")
    def test_retrieve_observation_notes(self, auth_service):
        module_configs = [MagicMock()]
        user_id = SAMPLE_ID
        skip = limit = 0
        self.service.retrieve_observation_notes(module_configs, user_id, skip, limit)
        self.repo.retrieve_primitives.assert_called_with(
            user_id,
            QuestionnaireModule.moduleId,
            Questionnaire.__name__,
            0,
            0,
            SortField.Direction.ASC,
            field_filter={
                Primitive.MODULE_CONFIG_ID: {VALUE_IN: [i.id for i in module_configs]}
            },
        )
        auth_service().retrieve_user_profiles_by_ids.assert_called_with(set())

    def test_delete_user_primitive(self):
        user_id = SAMPLE_ID
        self.service.delete_user_primitive(user_id)
        self.deployment_service().retrieve_modules.assert_called_once()
        self.repo.delete_user_primitive.assert_called_with(
            session=None, user_id=user_id, primitive_names=[]
        )

    def test_retrieve_unseen_module_results_no_flags(self):
        self.repo.retrieve_unseen_results.return_value = [
            {"flags": {"red": 1, "amber": 0, "gray": 0}},
            {"flags": {"red": 0, "amber": 1, "gray": 0}},
            {"flags": {"red": 0, "amber": 0, "gray": 0}},
        ]
        self.repo.retrieve_first_unseen_result.return_value = None
        req_obj = RetrieveUnseenModuleResultRequestObject()
        result = self.service.retrieve_unseen_module_results(req_obj)
        self.assertEqual(2, len(result.flags))


if __name__ == "__main__":
    unittest.main()
