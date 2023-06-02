from extensions.common.sort import SortField
from extensions.module_result.models.primitives import Primitives, CVDRiskScore
from extensions.module_result.modules.visualizer import HTMLVisualizer
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from sdk.common.utils.inject import autoparams


class CardiovascularHTMLVisualizer(HTMLVisualizer):
    TITLE = "Cardiovascular Risk"
    template_name = "cardiovascular.html"

    def get_context(self) -> dict:
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        if not config:
            return {}

        with self.module.configure(config):
            primitives: list[CVDRiskScore] = self._fetch_primitives()  # noqa
            if not len(primitives):
                return {}

        data, factors = self._build_data(primitives[0])
        return {
            "title": config.moduleName or self.TITLE,
            "cardiovascular_data": data,
            "cardiovascular_factors": factors,
        }

    @staticmethod
    def _build_data(primitive: CVDRiskScore):
        risk_factors_list = [
            {
                "name": "Age",
                "imgSrc": "https://huma-static-assets.netlify.app/pdf-template-assest/Heart.png",
                "title": "Age",
            },
            {
                "name": "Medical History",
                "imgSrc": "https://huma-static-assets.netlify.app/pdf-template-assest/Medication.png",
                "title": "Medical history",
            },
            {
                "name": "Sex",
                "imgSrc": "https://huma-static-assets.netlify.app/pdf-template-assest/Gender.png",
                "title": "Biological sex",
            },
            {
                "name": "Health Rating",
                "imgSrc": "https://huma-static-assets.netlify.app/pdf-template-assest/Track.png",
                "title": "Health rating",
            },
            {
                "name": "Body Measurements",
                "imgSrc": "https://huma-static-assets.netlify.app/pdf-template-assest/Measure.png",
                "title": "Body measurements",
            },
            {
                "name": "Physical Activity",
                "imgSrc": "https://huma-static-assets.netlify.app/pdf-template-assest/Running.png",
                "title": "Physical activity",
            },
            {
                "name": "Heart Rate",
                "imgSrc": "https://huma-static-assets.netlify.app/pdf-template-assest/Heart Rate.png",
                "title": "Heart rate",
            },
        ]
        risk_factors_dict = {}
        for risk_factor in primitive.riskFactors:
            risk_factors_dict[risk_factor.name.value] = {
                "status": risk_factor.status,
            }
        factors = []
        for factor in risk_factors_list:
            factors.append(
                {
                    **risk_factors_dict.get(factor["name"]),
                    "statusClass": "cardiovascular-risk",
                    "imgSrc": factor["imgSrc"],
                    "title": factor["title"],
                }
            )

        data = []
        for ind, trajectory in enumerate(primitive.riskTrajectory):
            data.append({"date": ind, "value": trajectory.riskPercentage})

        if len(data):
            data[0]["value"] = 0

        return data, factors

    @autoparams("repo")
    def _fetch_primitives(self, repo: ModuleResultRepository) -> Primitives:
        primitives = repo.retrieve_primitives(
            user_id=self.user.id,
            module_id=self.module.moduleId,
            primitive_name=CVDRiskScore.__name__,
            skip=0,
            limit=1,
            direction=SortField.Direction.DESC,
            module_config_id=self.module.config.id,
        )
        self._apply_timezone_to_primitives(primitives)
        return primitives
