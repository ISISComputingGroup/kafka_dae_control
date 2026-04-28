from kafka_dae_control.data import ObservableField


def test_observable_field_initial_value_field():
    field = ObservableField(123)

    assert field.value == 123


def test_observable_field_attach_and_set_value_calls_callback():
    field = ObservableField("old")
    calls = []

    def callback(old_value: str, new_value: str) -> None:
        calls.append((old_value, new_value))

    field.attach(callback)
    field.value = "new"

    assert field.value == "new"
    assert calls == [("old", "new")]


def test_observable_field_calls_callbacks_in_attachment_order():
    field = ObservableField(1)
    calls = []

    field.attach(lambda old_value, new_value: calls.append(("first", old_value, new_value)))
    field.attach(lambda old_value, new_value: calls.append(("second", old_value, new_value)))

    field.value = 2

    assert calls == [
        ("first", 1, 2),
        ("second", 1, 2),
    ]
