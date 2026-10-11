from datetime import date

from app.api.utils import get_data_product_download_name, sanitize_file_name_part

acquisition_date = date(2022, 7, 25)


def test_download_name_combines_project_date_and_data_type() -> None:
    """The name is built from the project, flight date, and data type."""
    assert (
        get_data_product_download_name(
            "Corn Trial 2024", acquisition_date, "Orthomosaic", ".jpg"
        )
        == "Corn_Trial_2024_20220725_Orthomosaic.jpg"
    )


def test_download_name_neutralizes_path_separators() -> None:
    """Path separators cannot survive into the file name."""
    name = get_data_product_download_name(
        "../../etc/passwd", acquisition_date, "dsm", ".jpg"
    )

    assert "/" not in name
    assert ".." not in name
    assert name == "etc_passwd_20220725_dsm.jpg"


def test_download_name_neutralizes_shell_and_quote_characters() -> None:
    """Quotes and shell metacharacters are stripped from every component."""
    name = get_data_product_download_name(
        'Trial"; rm -rf /', acquisition_date, "a\nb", ".jpg"
    )

    assert all(char not in name for char in ('"', ";", "\n", "/"))


def test_download_name_does_not_leave_a_dot_inside_the_stem() -> None:
    """A dotted project title cannot be read as a file extension."""
    name = get_data_product_download_name("Trial v1.2", acquisition_date, "DSM", ".tif")

    assert name == "Trial_v1_2_20220725_DSM.tif"
    # only the real extension separator remains
    assert name.count(".") == 1


def test_download_name_keeps_compound_extensions() -> None:
    """Compound extensions such as .copc.laz keep their separating dot."""
    name = get_data_product_download_name(
        "Corn Trial", acquisition_date, "point_cloud", ".copc.laz"
    )

    assert name == "Corn_Trial_20220725_point_cloud.copc.laz"


def test_download_name_truncates_long_components() -> None:
    """Long titles and data types cannot push the name past filesystem limits."""
    name = get_data_product_download_name(
        "P" * 300, acquisition_date, "D" * 300, ".jpg"
    )

    assert len(name) < 255
    assert name.startswith("P" * 48 + "_20220725_")


def test_download_name_falls_back_to_the_date_alone() -> None:
    """Components that sanitize away are dropped rather than leaving separators."""
    name = get_data_product_download_name("   ", acquisition_date, "***", ".jpg")

    assert name == "20220725.jpg"


def test_download_name_never_uses_the_uploaded_file_name() -> None:
    """The uploaded name is not an input, so it cannot leak into a download."""
    name = get_data_product_download_name("Corn Trial", acquisition_date, "dsm", ".jpg")

    assert "malicious" not in name


def test_sanitize_file_name_part_strips_and_collapses() -> None:
    """Components are whitelisted, collapsed, and trimmed."""
    assert sanitize_file_name_part("  Corn // Trial  ") == "Corn_Trial"
    assert sanitize_file_name_part("___") == ""
    assert sanitize_file_name_part("keeps-hyphens_and_1234") == "keeps-hyphens_and_1234"


def test_download_name_truncates_multi_byte_components_by_bytes() -> None:
    """The per-part cap is a byte budget, not a character count.

    \\w is Unicode aware, so a character based cap would let a title of four byte
    characters push the joined name past the 255 byte filesystem limit. The export
    writes this name to disk, where exceeding the limit is an OSError.
    """
    # U+20000 is a word character that encodes to four bytes in UTF-8
    name = get_data_product_download_name(
        "\U00020000" * 300, acquisition_date, "\U00020000" * 300, ".jpg"
    )

    assert len(name.encode("utf-8")) < 255


def test_sanitize_file_name_part_caps_bytes_not_characters() -> None:
    """A component is trimmed to fit the byte budget, splitting no character."""
    part = sanitize_file_name_part("\U00020000" * 100)

    assert len(part.encode("utf-8")) <= 48
    # a character based cap would have kept 48 characters, or 192 bytes
    assert len(part) == 12
