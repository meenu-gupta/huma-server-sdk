from sdk.common.utils.convertible import convertibleclass, meta, required_field

from .primitive import Primitive


@convertibleclass
class OARS(Primitive):

    OARS_SCORE = "oarsScore"
    PAIN_SCORE = "painScore"
    SLEEP_SCORE = "sleepScore"
    NAUSEA_SCORE = "nauseaScore"
    MOBILITY_SCORE = "mobilityScore"

    painScore: float = required_field()
    sleepScore: float = required_field(metadata=meta(value_to_field=float))
    nauseaScore: float = required_field(metadata=meta(value_to_field=float))
    mobilityScore: float = required_field(metadata=meta(value_to_field=float))
    oarsScore: float = required_field(metadata=meta(value_to_field=float))

    _scoring_answers = None

    @property
    def scoring_answers(self):
        return self._scoring_answers

    @scoring_answers.setter
    def scoring_answers(self, value):
        self._scoring_answers = value

    @classmethod
    def field_to_ids_map(cls):
        return {
            cls.SLEEP_SCORE: {"oars_10", "oars_11", "oars_12"},
            cls.PAIN_SCORE: {"oars_2", "oars_4", "oars_5", "oars_6"},
            cls.NAUSEA_SCORE: {"oars_1", "oars_3", "oars_13", "oars_14"},
            cls.MOBILITY_SCORE: {"oars_7", "oars_8", "oars_9"},
        }
