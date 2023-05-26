from dataclasses import asdict, dataclass


@dataclass
class DictHelperMixin:
    def to_dict(self):
        self_dict = asdict(self)
        for key, value in self_dict.items():
            if isinstance(value, DictHelperMixin):
                self_dict[key] = value.to_dict()

        return self_dict


@dataclass
class DTOrder(DictHelperMixin):
    index: int
    column: int
    direction: str  # asc/desc

    def __str__(self):
        return f'index: {self.index} column: {self.column}, direction: {self.direction}'


@dataclass
class DTColumn(DictHelperMixin):
    data: str
    name: str
    searchable: bool
    orderable: bool
    search_value: str
    search_is_regex: bool

    def __str__(self):
        return f'data: {self.data}, name: {self.name}'


@dataclass
class DTRequest(DictHelperMixin):
    draw: int
    start: int
    length: int
    search_value: str
    search_regex: bool
    columns: DTColumn
    orders: DTOrder
