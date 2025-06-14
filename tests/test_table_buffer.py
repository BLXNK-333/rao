import pytest
from unittest.mock import patch

from src.frontend.widgets.table import TableBuffer  # путь к модулю с TableBuffer
from src.enums import EventType, GROUP
from src.eventbus import EventBus


@pytest.fixture(autouse=True)
def patch_eventbus_publish():
    with patch.object(EventBus, "publish") as pub_mock, \
         patch.object(EventBus, "subscribe") as sub_mock:
        yield pub_mock, sub_mock


@pytest.fixture
def table_buffer():
    return TableBuffer(
        group_id=GROUP.SONGS_TABLE,
        original_data={},
        header_map={}
    )

@pytest.fixture
def buffer_for_sort_tests():
    return TableBuffer(
        group_id=GROUP.SONGS_TABLE,
        original_data={},
        header_map={}
    )



def test_initial_state(table_buffer):
    assert table_buffer._group_id == GROUP.SONGS_TABLE
    assert table_buffer.original_data == {}
    assert table_buffer.sorted_keys == []
    assert table_buffer.history == []
    assert table_buffer.max_history == 10
    assert table_buffer.sort_key == (0, "", 0)
    assert table_buffer.filter_term == ""


@patch("src.frontend.widgets.table.EventBus.subscribe")
@patch("src.frontend.widgets.table.EventBus.publish")
def test_subscribe_called(mock_publish, mock_subscribe):
    TableBuffer(group_id=GROUP.SONGS_TABLE, original_data={}, header_map={})

    assert mock_subscribe.call_count == 4  # ✅ Проверка, что было ровно 4 подписки


def test_filter_data_with_term(table_buffer, patch_eventbus_publish):
    pub_mock, _ = patch_eventbus_publish

    table_buffer.original_data = {
        "1": ["Alpha", "Beta"],
        "2": ["Gamma", "Delta"],
        "3": ["AlphaGamma", "Epsilon"]
    }
    table_buffer.sorted_keys = ["1", "2", "3"]

    table_buffer.filter_data("alpha")

    filtered_call = pub_mock.call_args
    assert filtered_call is not None

    event_arg, data_arg, is_full_table = filtered_call[0]

    assert event_arg.event_type == EventType.VIEW.TABLE.BUFFER.FILTERED_TABLE
    assert data_arg == [
        ["Alpha", "Beta"],
        ["AlphaGamma", "Epsilon"]
    ]
    assert is_full_table == False


def test_filter_data_with_empty_term(table_buffer, patch_eventbus_publish):
    pub_mock, _ = patch_eventbus_publish
    table_buffer.original_data = {
        "1": ["a", "b"],
        "2": ["c", "d"]
    }
    table_buffer.sorted_keys = ["1", "2"]

    table_buffer.filter_data("")
    _, data_arg, _ = pub_mock.call_args[0]
    assert len(data_arg) == 2  # returns all


def test_sort_data_string_column(table_buffer):
    table_buffer.original_data = {
        "1": ["b", "2"],
        "2": ["a", "1"]
    }
    table_buffer.sort_data(None, (0, "Name", 1))
    assert table_buffer.sorted_keys == ["2", "1"]


def test_sort_data_numeric_column(table_buffer):
    table_buffer.original_data = {
        "1": ["5", "x"],
        "2": ["2", "y"]
    }
    table_buffer.sort_data(None, (0, "ID", 1))
    assert table_buffer.sorted_keys == ["2", "1"]


def test_sort_data_handles_exception(table_buffer):
    table_buffer.original_data = {
        "1": ["abc"],
        "2": ["xyz"]
    }
    # column index out of range
    table_buffer.sort_data(None, (3, "ID", 1))
    assert set(table_buffer.sorted_keys) == set(["1", "2"])


def test_update_item_sorts_and_publishes(table_buffer, patch_eventbus_publish):
    pub_mock, _ = patch_eventbus_publish
    table_buffer.original_data = {}
    table_buffer.sort_key = (0, "ID", 1)

    table_buffer.update_item(["42", "Hello"])
    assert "42" in table_buffer.original_data
    assert pub_mock.call_args_list[-1][0][0].event_type == EventType.VIEW.TABLE.BUFFER.CARD_UPDATED


def test_delete_items_removes_ids(table_buffer):
    table_buffer.original_data = {
        "1": ["a"],
        "2": ["b"]
    }
    table_buffer.sorted_keys = ["1", "2"]
    table_buffer.history = [("a", ["1", "2"])]

    table_buffer.delete_items(["1"], GROUP.SONGS_TABLE)
    assert "1" not in table_buffer.original_data
    assert table_buffer.sorted_keys == ["2"]
    assert table_buffer.history == []


def test_filter_history_adds_new_terms(table_buffer):
    table_buffer.sorted_keys = ["1", "2", "3"]
    table_buffer.original_data = {
        "1": ["apple"],
        "2": ["banana"],
        "3": ["apricot"]
    }

    table_buffer.filter_data("a")
    assert table_buffer.history[-1][0] == "a"
    initial_len = len(table_buffer.history)

    table_buffer.filter_data("ap")
    assert table_buffer.history[-1][0] == "ap"
    assert len(table_buffer.history) == initial_len + 1


def test_filter_history_with_empty_term(table_buffer):
    table_buffer.sorted_keys = ["1", "2"]
    table_buffer.original_data = {
        "1": ["a"],
        "2": ["b"]
    }

    table_buffer.filter_data("")
    assert table_buffer.history[-1][0] == ""
    assert len(table_buffer.history) == 1


def test_filter_uses_history_prefix(table_buffer):
    # Добавим в историю ключи для 'a'
    table_buffer.sorted_keys = ["1", "2", "3"]
    table_buffer.original_data = {
        "1": ["apple"],
        "2": ["banana"],
        "3": ["apricot"]
    }

    table_buffer.history = [
        ("", ["1", "2", "3"]),
        ("a", ["1", "3"])  # ключи с 'a' в данных
    ]

    # Фильтруем с префиксом "ap", база должна быть ["1", "3"]
    table_buffer.filter_data("ap")
    # Последний элемент истории должен быть ("ap", keys), keys должны быть подмножеством ["1", "3"]
    last_term, last_keys = table_buffer.history[-1]
    assert last_term == "ap"
    assert all(k in ["1", "3"] for k in last_keys)


def test_history_length_limit(table_buffer):
    table_buffer.sorted_keys = []
    table_buffer.original_data = {}

    max_hist = table_buffer.max_history

    for i in range(max_hist + 5):
        term = f"term{i}"
        keys = [str(i)]
        table_buffer._update_history(term, keys)

    assert len(table_buffer.history) == max_hist
    # Проверяем, что первые элементы удалились
    assert table_buffer.history[0][0] == f"term5"


def test_sort_clears_history(table_buffer):
    table_buffer.history = [("t", ["1"]), ("tes", ["1"]), ("test", ["1"])]
    table_buffer.sorted_keys = ["1", "2"]
    table_buffer.original_data = {
        "1": ["a", "x"],
        "2": ["b", "y"]
    }
    table_buffer.filter_term = "a"

    table_buffer.sort_data(None, (0, "Name", 1))

    # История должна быть очищена, а потом заполнена новым фильтром 'a'
    assert len(table_buffer.history) == 1
    assert table_buffer.history[0][0] == "a"


def test_sort_key_id(buffer_for_sort_tests):
    buf = buffer_for_sort_tests
    buf.original_data = {
        "1": ["5", "dummy"],
        "2": ["10", "dummy"]
    }
    # Передаем column_name в нижнем регистре "id"
    assert buf._sort_key("1", 0, "id") < buf._sort_key("2", 0, "id")


def test_sort_key_time(buffer_for_sort_tests):
    buf = buffer_for_sort_tests
    buf.original_data = {
        "1": ["ignored", "02:00"],
        "2": ["ignored", "11:00"],
        "3": ["ignored", "02:00:05"],
        "4": ["ignored", "invalid"]
    }

    # column_name в нижнем регистре
    key1 = buf._sort_key("1", 1, "time")
    key2 = buf._sort_key("2", 1, "time")
    key3 = buf._sort_key("3", 1, "time")
    key4 = buf._sort_key("4", 1, "time")  # должно быть float('inf')

    assert key1[0] < key2[0]
    assert key3[0] > key1[0]
    assert key4[0] == float('inf')


def test_sort_key_fallback_to_string(buffer_for_sort_tests):
    buf = buffer_for_sort_tests
    buf.original_data = {
        "1": ["ignored", "Apple"],
        "2": ["ignored", "banana"]
    }

    key1 = buf._sort_key("1", 1, "Other")
    key2 = buf._sort_key("2", 1, "Other")

    assert key1[0] < key2[0]  # "apple" < "banana"


def test_find_insert_position_no_sort(buffer_for_sort_tests):
    buf = buffer_for_sort_tests
    buf.original_data = {
        "1": ["1", "aaa"],
        "2": ["2", "bbb"]
    }
    buf.sorted_keys = ["1", "2"]
    buf.sort_key = (0, "ID", 0)  # no sort

    # Добавим новый элемент
    buf.original_data["3"] = ["3", "ccc"]
    pos = buf._find_insert_position("3", was_present=False)
    assert pos == 2  # вставка в конец


def test_find_insert_position_sorted(buffer_for_sort_tests):
    buf = buffer_for_sort_tests
    buf.original_data = {
        "1": ["10", "aaa"],
        "2": ["20", "bbb"],
        "3": ["15", "ccc"]
    }
    buf.sorted_keys = ["1", "2"]
    buf.sort_key = (0, "ID", 1)

    pos = buf._find_insert_position("3", was_present=False)
    assert pos == 1  # между 10 и 20


def test_insert_sorted_key(buffer_for_sort_tests):
    buf = buffer_for_sort_tests
    buf.original_data = {
        "1": ["10", "aaa"],
        "2": ["20", "bbb"],
        "3": ["15", "ccc"]
    }
    buf.sorted_keys = ["1", "2"]
    buf.sort_key = (0, "ID", 1)

    buf._insert_sorted_key("3")
    assert buf.sorted_keys == ["1", "3", "2"]


def test_find_insert_position_no_sort_existing_key(buffer_for_sort_tests):
    buf = buffer_for_sort_tests
    buf.original_data = {
        "1": ["1", "aaa"],
        "2": ["2", "bbb"]
    }
    buf.sorted_keys = ["1", "2"]
    buf.sort_key = (0, "ID", 0)  # no sort

    # Обновляем существующий элемент
    pos = buf._find_insert_position("1", was_present=True, old_pos=0)
    assert pos == 0  # останется на своём месте, без сортировки


def test_find_insert_position_sorted_existing_key(buffer_for_sort_tests):
    buf = buffer_for_sort_tests
    buf.original_data = {
        "1": ["10", "aaa"],
        "2": ["20", "bbb"],
        "3": ["15", "ccc"]
    }
    buf.sorted_keys = ["1", "2", "3"]
    buf.sort_key = (0, "ID", 1)

    # Ключ уже в списке, проверим, куда он будет вставлен повторно
    pos = buf._find_insert_position("3", was_present=True)
    assert pos == 1  # ключ со значением "15" должен быть между "10" и "20"
