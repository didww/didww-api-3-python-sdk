class QueryParams:
    def __init__(self):
        self._filters = {}
        self._sort = []
        self._include = []
        self._page = {}

    def filter(self, key, value):
        self._filters[key] = value
        return self

    def sort(self, *fields):
        self._sort.extend(fields)
        return self

    def include(self, *resources):
        self._include.extend(resources)
        return self

    def page(self, number=None, size=None):
        if number is not None:
            self._page["number"] = number
        if size is not None:
            self._page["size"] = size
        return self

    def to_dict(self):
        params = {}
        for key, value in self._filters.items():
            params[f"filter[{key}]"] = value
        if self._sort:
            params["sort"] = ",".join(self._sort)
        if self._include:
            params["include"] = ",".join(self._include)
        for key, value in self._page.items():
            params[f"page[{key}]"] = value
        return params
