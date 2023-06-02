from extensions.module_result.models.primitives.primitive_oxford_hip import (
    OxfordHipScore,
    HipAffected,
    HipData,
)


class OxfordHipScoreCalculator:
    def calculate(self, primitive: OxfordHipScore):
        hips_data = primitive.hipsData

        if primitive.hipAffected == HipAffected.BOTH.value:
            self._process_right_hip_data(primitive, hips_data[0])
            self._process_left_hip_data(primitive, hips_data[1])
        else:
            if primitive.hipAffected == HipAffected.RIGHT.value:
                self._process_right_hip_data(primitive, hips_data[0])
            else:
                self._process_left_hip_data(primitive, hips_data[0])

    def _process_right_hip_data(self, primitive: OxfordHipScore, hip_data: HipData):
        hip_score = self._calculate_hip_score(hip_data)
        primitive.rightHipScore = hip_score
        hip_data.set_score(HipAffected.RIGHT, hip_score)

    def _process_left_hip_data(self, primitive: OxfordHipScore, hip_data: HipData):
        hip_score = self._calculate_hip_score(hip_data)
        primitive.leftHipScore = hip_score
        hip_data.set_score(HipAffected.LEFT, hip_score)

    def _calculate_hip_score(self, hip_data: HipData) -> int:
        hip_dict = hip_data.to_dict()
        answer_scores = self._map_answers_with_scores(hip_dict.values())
        return sum(answer_scores)

    @staticmethod
    def _map_answers_with_scores(answers: list[int]) -> list[int]:
        score_mapping = {i: 5 - i for i in range(1, 6)}
        return [score_mapping.get(v, 0) for v in answers]
