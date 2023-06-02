import csv
import io
import json
import os
import shutil
import tempfile
from typing import Any
import wave
from datetime import datetime
from random import shuffle
from tempfile import NamedTemporaryFile

from bson import ObjectId
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

from extensions.common.s3object import S3Object
from extensions.revere.exceptions import HoundifyException
from extensions.revere.houndify.houndify import HoundifySDKError
from extensions.revere.models.revere import RevereTestResult, RevereTest
from extensions.revere.repository.revere_repository import RevereTestRepository
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.exceptions.exceptions import InvalidRequestException, ObjectDoesNotExist
from sdk.common.localization.utils import Language
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig
from extensions.revere.houndify import houndify


class RevereTestService:
    """Service to work  with revere repo."""

    @autoparams()
    def __init__(
        self,
        repo: RevereTestRepository,
        fs: FileStorageAdapter,
        config: PhoenixServerConfig,
    ):
        self.repo = repo
        self.fs = fs
        self.revereConfig = config.server.revereTest

    def create_test(
        self, user_id: str, deployment_id: str, module_name: str
    ) -> tuple[str, list[dict[str, Any]]]:
        words_list = self.retrieve_word_lists_for_test()
        test_id = self.repo.create_test(
            user_id=user_id, deployment_id=deployment_id, module_name=module_name
        )
        return test_id, words_list

    def retrieve_test(self, user_id: str, test_id: str) -> RevereTest:
        return self.repo.retrieve_test(test_id=test_id, user_id=user_id)

    def finish_test(self, user_id, test_id):
        return self.repo.finish_test(user_id=user_id, test_id=test_id)

    def retrieve_user_tests(self, user_id: str, status=None) -> list[RevereTest]:
        return self.repo.retrieve_user_tests(user_id=user_id, status=status)

    def export_test_result(self, user_id: str, test_id: str) -> str:
        """Used to generate csv table with test results"""
        test = self.repo.retrieve_test(user_id=user_id, test_id=test_id)

        columns = ["A", "1", "2", "3", "4", "5", "7", "8", "B", "6"]
        rows = [columns]
        a, b = self.retrieve_initial_word_lists()
        matched_row = ["Total", 0, 0, 0, 0, 0, 0, 0, None, 0]
        for word in a:
            index = a.index(word)
            row = [word, None, None, None, None, None, None, None, b[index], None]
            for word_list in test.results[:8]:
                row_ind = test.results.index(word_list)
                result_word_list = [w.lower() for w in word_list.wordsResult]
                check_word = word.lower()
                # moving result for B to the end
                if row_ind == 5:
                    row_ind = 8
                    check_word = b[index].lower()
                # moving 6th and 7th in list because of #5 goes to end
                if row_ind in (6, 7):
                    # skipping B column
                    row_ind -= 1
                matched = "Y" if check_word in result_word_list else "N"
                if matched == "Y":
                    matched_row[row_ind + 1] += 1
                row[row_ind + 1] = matched
            rows.append(row)

        rows.append(matched_row)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        return output.getvalue()

    def process_audio_result(
        self, s3_audio_file: S3Object, language: str = Language.EN_GB
    ):
        file = self.retrieve_audio_file(s3_audio_file)
        with NamedTemporaryFile() as tmp:
            tmp.write(file.read())
            try:
                mp4_version = AudioSegment.from_file(tmp.name, "mp4")
            except CouldntDecodeError:
                raise InvalidRequestException(
                    "Invalid file format, check if the file is an mp4"
                )
            mp4_version = mp4_version.set_frame_rate(16000)
        with NamedTemporaryFile() as tmp:
            mp4_version.export(tmp.name, "wav", codec="pcm_s16le")
            audio = wave.open(tmp.name)

        result = self._get_houndify_result(language, audio)
        words = result["AllResults"][0].get("RawTranscription", "")
        words = words.split(" ")
        build_number = result.get("BuildInfo", {}).get("BuildNumber")
        extra_info = {
            RevereTestResult.BUILD_NUMBER: build_number,
            RevereTestResult.INPUT_LANGUAGE_IETF_TAG: language,
        }
        return words, extra_info

    def _get_houndify_result(self, language: str, audio: wave.Wave_read):
        try:
            client = houndify.StreamingHoundClient(
                self.revereConfig.clientId, self.revereConfig.clientKey, "revere-user"
            )
            client.setHoundRequestInfo("InputLanguageIETFTag", language)
            client.setSampleRate(audio.getframerate())
            client.start()

            while True:
                samples = audio.readframes(256)
                if len(samples) == 0:
                    break
                if client.fill(samples):
                    break

            result = client.finish()
        except HoundifySDKError:
            raise HoundifyException
        except Exception as e:
            raise InvalidRequestException(str(e))
        return result

    def save_word_list_result(
        self,
        test_id,
        user_id,
        result: RevereTestResult,
    ):
        result.wordsResult = self.process_homophones(result.wordsResult)
        test = self.repo.retrieve_test(user_id=user_id, test_id=test_id)
        if len(test.results) > 7:
            raise InvalidRequestException("Max amount of results already submitted")

        self.repo.save_word_list_result(
            test_id=test_id,
            user_id=user_id,
            result=result,
        )

    def process_homophones(self, words):
        homophones_dict = self.repo.retrieve_homophones()
        result = []
        prev = words[0]
        prev_ind = 0
        pairs_data = {}

        # Gathering pairs of words to process double-worded homophones
        for word in words[1:]:
            pair = f"{prev}+{word}".lower()
            pairs_data[pair] = [prev_ind, prev_ind + 1]
            prev = word
            prev_ind += 1

        # replacing pair of words with correct word
        for pair in pairs_data:
            if pair in homophones_dict.keys():
                word = homophones_dict[pair]
                del words[pairs_data[pair][0]]
                del words[pairs_data[pair][1]]
                words.insert(pairs_data[pair][0], word)

        # Processing single homophones
        for word in words:
            word = word.lower()
            if word in homophones_dict.keys():
                word = homophones_dict[word]
            result.append(word)
        return result

    def retrieve_audio_file(self, s3_audio_file: S3Object):
        if not self.fs.file_exist(s3_audio_file.bucket, s3_audio_file.key):
            raise ObjectDoesNotExist(
                f'Revere Audio at bucket "{s3_audio_file.bucket}" with '
                f'key "{s3_audio_file.key}" does not exist'
            )
        data, data_len, headers = self.fs.download_file(
            s3_audio_file.bucket, s3_audio_file.key
        )
        return data

    def retrieve_word_lists_for_test(self) -> list[dict[str, Any]]:
        a, b = self.retrieve_initial_word_lists()
        initial_a = a.copy()
        # initially shuffling word-list B
        shuffle(b)
        test_word_lists = []
        for i in range(8):
            if i < 5:
                shuffle(a)
            word_list = b if i == 5 else a.copy()
            word_list = initial_a if i > 5 else word_list  # keeping last 2 lists as is
            test_word_list_dict = {
                RevereTestResult.ID: str(ObjectId()),
                RevereTestResult.INITIAL_WORDS: word_list,
            }
            test_word_lists.append(test_word_list_dict)
        return test_word_lists

    def retrieve_initial_word_lists(self) -> tuple[list[str], list[str]]:
        return self.repo.retrieve_initial_word_lists()

    def export_tests_zip(self, user_id: str, status: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tests = self.retrieve_user_tests(user_id=user_id, status=status)
            tests = [
                test.to_dict(
                    ignored_fields=[
                        "id",
                        "userId",
                        "results.id",
                        "results.userId",
                        "results.deploymentId",
                        "results.submitterId",
                    ]
                )
                for test in tests
            ]
            results_dir = f"{tmp_dir}/results/"
            os.mkdir(results_dir)
            with open(f"{results_dir}/response.json", "w") as resp_f:
                resp_f.write(json.dumps(tests, indent=4))
            for d in tests:
                test_id = d["id"]
                start_date = d["startDateTime"]
                user_id = d["userId"]
                test_dir = f"{results_dir}/{test_id}_{start_date}"
                os.mkdir(test_dir)
                counter = 0
                # audio
                for result in d["results"]:
                    counter += 1
                    key = result["audioResult"]["key"]
                    bucket = result["audioResult"]["bucket"]
                    audio = self.fs.download_file(bucket, key)
                    with open(f"{test_dir}/{test_id}_0{counter}.m4a", "wb") as audio_f:
                        audio_f.write(audio[0].read())
                # tables
                table = self.export_test_result(user_id=user_id, test_id=test_id)
                with open(f"{test_dir}/{test_id}_{start_date}.csv", "w") as csv_f:
                    csv_f.write(table)
            archive_filename = shutil.make_archive(
                f"{tmp_dir}/{user_id}_{datetime.now()}.zip", "zip", results_dir
            )
            with open(archive_filename, "rb") as archive:
                return archive.read()
