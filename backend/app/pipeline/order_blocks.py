from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import Block, PageResult


@dataclass(frozen=True)
class _SortableBlock:
    block: Block
    x1: float
    y1: float
    x2: float

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2.0


def _to_sortable(block: Block) -> _SortableBlock:
    x1, y1, x2, _ = block.bbox
    return _SortableBlock(block=block, x1=x1, y1=y1, x2=x2)


def _estimate_page_width(items: list[_SortableBlock], page_width: int) -> float:
    if page_width > 0:
        return float(page_width)
    if not items:
        return 1.0
    max_x = max(item.x2 for item in items)
    min_x = min(item.x1 for item in items)
    return max(max_x - min_x, 1.0)


def _choose_two_column_split(items: list[_SortableBlock], estimated_width: float) -> float | None:
    if len(items) < 6:
        return None

    centers = sorted(item.center_x for item in items)
    largest_gap = 0.0
    split_x: float | None = None
    for left, right in zip(centers, centers[1:], strict=False):
        gap = right - left
        if gap > largest_gap:
            largest_gap = gap
            split_x = (left + right) / 2.0

    if split_x is None:
        return None
    # If the horizontal gap is large enough, treat as two columns.
    if largest_gap < estimated_width * 0.14:
        return None

    left_count = sum(1 for item in items if item.center_x <= split_x)
    right_count = len(items) - left_count
    if left_count < 2 or right_count < 2:
        return None
    return split_x


def _sort_in_reading_order(blocks: list[Block], page_width: int) -> list[Block]:
    items = [_to_sortable(block) for block in blocks]
    if not items:
        return []

    estimated_width = _estimate_page_width(items, page_width)
    split_x = _choose_two_column_split(items, estimated_width)
    if split_x is None:
        ordered = sorted(items, key=lambda item: (item.y1, item.x1))
        return [item.block for item in ordered]

    left_items = [item for item in items if item.center_x <= split_x]
    right_items = [item for item in items if item.center_x > split_x]
    left_sorted = sorted(left_items, key=lambda item: (item.y1, item.x1))
    right_sorted = sorted(right_items, key=lambda item: (item.y1, item.x1))
    return [item.block for item in [*left_sorted, *right_sorted]]


def order_page_blocks(page: PageResult) -> PageResult:
    ordered = _sort_in_reading_order(page.blocks, page.img_w)
    return page.model_copy(update={"blocks": ordered})

