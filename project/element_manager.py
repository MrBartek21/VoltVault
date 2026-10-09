# -*- coding: utf-8 -*-

from sd_manager import SDManager


class ElementManager:

    def __init__(self, sd: SDManager, filename="elements.json"):
        self.sd = sd
        self.filename = filename
        self.elements = {}
        self.load_elements()

    # -------------------- HELPERS --------------------

    @staticmethod
    def normalize(text: str) -> str:
        """Lowercase and strip text for consistent comparison."""
        return text.strip().lower() if isinstance(text, str) else ""

    # -------------------- LOAD / SAVE --------------------

    def load_elements(self):
        """Load elements using SDManager."""
        data = self.sd.read_file(self.filename)
        if isinstance(data, dict):
            self.elements = data
        else:
            self.elements = {}

    def save_elements(self):
        """Save elements using SDManager."""
        self.sd.write_file(self.filename, self.elements)

    # -------------------- LIST --------------------

    def list_elements(self):
        """Return list of all elements."""
        return sorted(self.elements.values(), key=lambda item: str(item.get("nazwa", "")).casefold())

    # -------------------- ADD / UPDATE --------------------

    def add_or_update_element(self, element: dict):
        """
        Add new element.
        If element with same code + category exists, increase quantity.
        Otherwise, add as new element.
        """
        code = self.normalize(element.get("oznaczenie"))
        category = self.normalize(element.get("kategorie"))

        # Check existing elements
        for existing_id, existing in self.elements.items():
            if (
                self.normalize(existing.get("oznaczenie")) == code
                and self.normalize(existing.get("kategorie")) == category
            ):
                existing["ilosc"] = int(existing.get("ilosc", 0)) + int(element.get("ilosc", 1))
                self.save_elements()
                return

        # New element
        element_id = str(element["id"])
        element["ilosc"] = int(element.get("ilosc", 1))
        self.elements[element_id] = element
        self.save_elements()

    # -------------------- DELETE --------------------

    def delete_element(self, element_id: str):
        element_id = str(element_id)
        if element_id in self.elements:
            del self.elements[element_id]
            self.save_elements()

    # -------------------- EDIT --------------------

    def edit_element(self, element_id: str, updated_data: dict):
        element_id = str(element_id)
        if element_id in self.elements:
            # Prevent changing ID
            updated_data.pop("id", None)
            self.elements[element_id].update(updated_data)
            self.save_elements()

    # -------------------- SEARCH --------------------

    def search(self, query: str):
        """Search elements by id, code, name, or category (case insensitive)."""
        query_norm = self.normalize(query)
        results = []

        for el in self.elements.values():
            if (
                query_norm in self.normalize(str(el.get("id", "")))
                or query_norm in self.normalize(el.get("oznaczenie"))
                or query_norm in self.normalize(el.get("nazwa"))
                or query_norm in self.normalize(el.get("kategorie", ""))
            ):
                results.append(el)

        return results
