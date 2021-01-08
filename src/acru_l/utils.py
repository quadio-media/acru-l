from collections import deque
from typing import Mapping, Any, Union, Deque


def traverse(data: Mapping[str, Any], path: Union[str, Deque]):
    if isinstance(path, str):
        path = path.split(".")
        path = deque(path)
    step = path.popleft()
    data = data[step]
    if path:
        return traverse(data, path)
    return data
