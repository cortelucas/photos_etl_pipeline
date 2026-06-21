"""Testes unitários de chunk_list."""

import pytest

from photos_etl.pipeline.chunking import chunk_list


class TestChunkList:
    def test_splits_list_into_chunks_of_given_size(self) -> None:
        items = [1, 2, 3, 4, 5]

        result = list(chunk_list(items, chunk_size=2))

        assert result == [[1, 2], [3, 4], [5]]

    def test_returns_single_chunk_when_chunk_size_is_larger_than_list(self) -> None:
        items = [1, 2, 3]

        result = list(chunk_list(items, chunk_size=10))

        assert result == [[1, 2, 3]]

    def test_returns_empty_iterator_when_list_is_empty(self) -> None:
        result = list(chunk_list([], chunk_size=5))

        assert result == []

    def test_each_chunk_has_exact_size_when_list_is_evenly_divisible(self) -> None:
        items = list(range(10))

        result = list(chunk_list(items, chunk_size=5))

        assert len(result) == 2
        assert all(len(chunk) == 5 for chunk in result)

    def test_preserves_original_order_across_chunks(self) -> None:
        items = list(range(20))

        result = list(chunk_list(items, chunk_size=7))
        flattened = [item for chunk in result for item in chunk]

        assert flattened == items

    def test_raises_value_error_when_chunk_size_is_zero(self) -> None:
        with pytest.raises(ValueError, match="chunk_size deve ser maior que zero"):
            list(chunk_list([1, 2, 3], chunk_size=0))

    def test_raises_value_error_when_chunk_size_is_negative(self) -> None:
        with pytest.raises(ValueError, match="chunk_size deve ser maior que zero"):
            list(chunk_list([1, 2, 3], chunk_size=-1))
