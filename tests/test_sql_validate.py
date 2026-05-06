import pytest

from chartmind.stages.sql_validate import SQLValidate, SQLValidationError


def test_select_is_read_only():
    draft = SQLValidate("sqlite").run("SELECT Name FROM Artist LIMIT 5")
    assert draft.is_read_only is True
    assert draft.referenced_tables == ["Artist"]


def test_select_with_join_extracts_all_tables():
    draft = SQLValidate("sqlite").run(
        "SELECT a.Name, COUNT(al.AlbumId) "
        "FROM Artist a JOIN Album al ON a.ArtistId = al.ArtistId "
        "GROUP BY a.Name"
    )
    assert draft.is_read_only is True
    assert set(draft.referenced_tables) == {"Artist", "Album"}


def test_delete_is_not_read_only():
    draft = SQLValidate("sqlite").run("DELETE FROM Artist WHERE ArtistId = 1")
    assert draft.is_read_only is False


def test_update_is_not_read_only():
    draft = SQLValidate("sqlite").run("UPDATE Artist SET Name = 'X' WHERE ArtistId = 1")
    assert draft.is_read_only is False


def test_drop_is_not_read_only():
    draft = SQLValidate("sqlite").run("DROP TABLE Artist")
    assert draft.is_read_only is False


def test_invalid_sql_raises():
    with pytest.raises(SQLValidationError):
        SQLValidate("sqlite").run("SELEC FROM WHERE")


def test_empty_sql_raises():
    with pytest.raises(SQLValidationError):
        SQLValidate("sqlite").run("   ")


def test_multiple_statements_rejected():
    with pytest.raises(SQLValidationError):
        SQLValidate("sqlite").run("SELECT 1; SELECT 2")


def test_trailing_semicolon_ok():
    draft = SQLValidate("sqlite").run("SELECT 1;")
    assert draft.is_read_only is True
