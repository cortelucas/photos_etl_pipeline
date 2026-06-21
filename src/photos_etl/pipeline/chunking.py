"""Utilitário de fatiamento de listas em lotes (chunks)."""

from collections.abc import Iterator
from typing import TypeVar

T = TypeVar("T")


def chunk_list[T](items: list[T], chunk_size: int) -> Iterator[list[T]]:
    """Divide uma lista em sublistas de tamanho no máximo chunk_size.

    Args:
        items: lista completa a ser fatiada.
        chunk_size: tamanho máximo de cada lote. Deve ser maior que zero.

    Yields:
        Sublistas consecutivas de items, preservando a ordem original.

    Raises:
        ValueError: se chunk_size não for maior que zero.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser maior que zero.")

    for start in range(0, len(items), chunk_size):
        yield items[start : start + chunk_size]
