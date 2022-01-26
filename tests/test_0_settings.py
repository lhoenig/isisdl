import os
from hashlib import sha256

from cryptography.hazmat.primitives.hashes import SHA3_512

from isisdl.settings import working_dir_location, _working_dir_location, database_file_location, checksum_algorithm, checksum_num_bytes, checksum_base_skip, sync_database_num_threads, \
    password_hash_iterations, \
    password_hash_algorithm, password_hash_length, \
    download_progress_bar_resolution, status_chop_off, status_time, env_var_name_username, env_var_name_password, enable_multithread, download_chunk_size, \
    sleep_time_for_isis, num_tries_download, download_timeout, download_timeout_multiplier, _status_time


def test_settings() -> None:
    assert working_dir_location == os.path.join(os.path.expanduser("~"), "test_isisdl")

    assert _working_dir_location == os.path.join(os.path.expanduser("~"), "isisdl_downloads")

    assert database_file_location == os.path.join(".state.db")

    assert checksum_algorithm == sha256

    assert password_hash_algorithm == SHA3_512

    assert env_var_name_username == "ISISDL_USERNAME"

    assert env_var_name_password == "ISISDL_PASSWORD"

    assert enable_multithread

    assert 1024 * 3 <= checksum_num_bytes <= 1024 * 5

    assert 1.5 <= checksum_base_skip <= 2.5

    assert 16 <= sync_database_num_threads <= 48

    assert 390_000 <= password_hash_iterations <= 1_000_000

    assert 32 <= password_hash_length <= 32

    assert 8 <= download_progress_bar_resolution <= 12

    assert 2 <= status_chop_off <= 3
    assert status_time == 2

    assert 0.1 <= _status_time <= 0.5

    assert 2 ** 13 <= download_chunk_size <= 2 ** 16

    assert 0 <= sleep_time_for_isis <= 4

    assert 3 <= num_tries_download <= 5

    assert 1 <= download_timeout <= 10

    assert 1.5 <= download_timeout_multiplier <= 2.5
