from typing import Dict, List

from beam.components import BaseComponent


class HTML:
    is_html = True

    def __init__(self, content):
        self.content = content


class VirtualField:
    is_virtual = True

    def __init__(self, verbose_name, callback):
        self.verbose_name = verbose_name
        self.callback = callback

    def get_value(self, obj=None):
        return self.callback(obj)


def layout_links(
    links: Dict[str, BaseComponent], link_layout: List[str]
) -> List[BaseComponent]:
    if not links:
        return []

    link_layout = link_layout or list(links.keys())
    hidden_names = {name[1:] for name in link_layout if name.startswith("!")}
    other_names = [
        name for name in links if name not in link_layout and name not in hidden_names
    ]

    laid_out = []
    for name in link_layout:
        if name == "...":
            for other_name in other_names:
                if links[other_name].show_link:
                    laid_out.append(links[other_name])
        elif name in links and name not in hidden_names and links[name].show_link:
            laid_out.append(links[name])

    return laid_out
