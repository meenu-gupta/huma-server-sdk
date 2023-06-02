from extensions.key_action.models.key_action_log import KeyAction


class Samples:
    @staticmethod
    def retrieve_key_actions_timeframe_request_body():
        return {
            "start": "2020-12-31T23:59:00.000Z",
            "end": "2021-01-01T00:00:00.000Z",
            "userId": "a733671100cd26d816eed39507",
            "timezone": "Europe/London",
        }

    @staticmethod
    def key_action(index=1):
        start = "2020-12-19T13:10:00.000Z"
        end = "2021-06-19T13:09:00.000Z"

        pattern = "DTSTART:20201220T100000\nRRULE:FREQ=DAILY;INTERVAL=210;UNTIL=20210619T130900;BYHOUR=10;BYMINUTE=0"
        return KeyAction(
            id=f"key_action_id{index}",
            model="KeyAction",
            recurrencePattern=pattern,
            keyActionConfigId="a733671100cd26d816eed39506",
            moduleId="Weight",
            moduleConfigId="a733671100cd26d816eed39502",
            isRecurring=True,
            startDateTime=start,
            endDateTime=end,
        )
