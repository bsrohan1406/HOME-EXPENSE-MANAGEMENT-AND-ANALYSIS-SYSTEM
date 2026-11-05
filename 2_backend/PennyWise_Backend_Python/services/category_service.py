"""
Category Service module for PennyWise Backend.

Handles business logic and database interactions
for Income and Expense categories.

Uses the approved MySQL categories schema:
- id
- name
- kind
- color
"""

from typing import Any, Dict, List, Optional

from database import execute_query, DatabaseError


class CategoryService:

    @staticmethod
    def normalize_category_type(category_type: str) -> str:
        """Validate and normalize category type."""

        if not category_type or not str(category_type).strip():
            raise ValueError("Category type is required.")

        normalized_type = str(category_type).strip().lower()

        if normalized_type not in ("income", "expense"):
            raise ValueError(
                "Category type must be either 'Income' or 'Expense'."
            )

        return normalized_type

    @staticmethod
    def get_all_categories(
        category_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all categories, optionally filtered by type."""

        if category_type:
            normalized_type = (
                CategoryService.normalize_category_type(category_type)
            )

            query = """
                SELECT
                    id AS category_id,
                    name,
                    kind AS type,
                    color
                FROM categories
                WHERE kind = %s
                ORDER BY name ASC
            """

            return execute_query(
                query,
                (normalized_type,),
                fetch_all=True
            )

        query = """
            SELECT
                id AS category_id,
                name,
                kind AS type,
                color
            FROM categories
            ORDER BY kind ASC, name ASC
        """

        return execute_query(query, fetch_all=True)

    @staticmethod
    def get_category_by_id(
        category_id: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a category using its ID."""

        query = """
            SELECT
                id AS category_id,
                name,
                kind AS type,
                color
            FROM categories
            WHERE id = %s
        """

        return execute_query(
            query,
            (category_id,),
            fetch_one=True
        )

    @staticmethod
    def get_category_by_name_and_type(
        name: str,
        category_type: str
    ) -> Optional[Dict[str, Any]]:
        """Check whether a category with the same name and type exists."""

        normalized_type = (
            CategoryService.normalize_category_type(category_type)
        )

        query = """
            SELECT
                id AS category_id,
                name,
                kind AS type,
                color
            FROM categories
            WHERE LOWER(name) = LOWER(%s)
            AND kind = %s
        """

        return execute_query(
            query,
            (name.strip(), normalized_type),
            fetch_one=True
        )

    @staticmethod
    def create_category(
        name: str,
        category_type: str,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new category."""

        if not name or not str(name).strip():
            raise ValueError(
                "Category name is required and cannot be empty."
            )

        clean_name = str(name).strip()

        if len(clean_name) > 50:
            raise ValueError(
                "Category name cannot exceed 50 characters."
            )

        clean_type = (
            CategoryService.normalize_category_type(category_type)
        )

        clean_color = (
            str(color).strip() if color is not None else None
        )

        # Check for duplicate category
        existing = CategoryService.get_category_by_name_and_type(
            clean_name,
            clean_type
        )

        if existing:
            raise ValueError(
                f"Category '{clean_name}' of type "
                f"'{clean_type}' already exists."
            )

        query = """
            INSERT INTO categories (name, kind, color)
            VALUES (%s, %s, %s)
        """

        category_id = execute_query(
            query,
            (clean_name, clean_type, clean_color),
            commit=True
        )

        created_category = CategoryService.get_category_by_id(
            category_id
        )

        if not created_category:
            raise DatabaseError(
                "Category was created but could not be retrieved."
            )

        return created_category

    @staticmethod
    def update_category(
        category_id: int,
        name: Optional[str] = None,
        category_type: Optional[str] = None,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing category."""

        category = CategoryService.get_category_by_id(category_id)

        if not category:
            raise KeyError(
                f"Category with ID {category_id} not found."
            )

        updated_name = category["name"]
        updated_type = category["type"]
        updated_color = category["color"]

        if name is not None:
            clean_name = str(name).strip()

            if not clean_name:
                raise ValueError(
                    "Category name cannot be empty."
                )

            if len(clean_name) > 50:
                raise ValueError(
                    "Category name cannot exceed 50 characters."
                )

            updated_name = clean_name

        if category_type is not None:
            updated_type = (
                CategoryService.normalize_category_type(category_type)
            )

        if color is not None:
            updated_color = str(color).strip() or None

        # Check for duplicate category
        if (
            updated_name != category["name"]
            or updated_type != category["type"]
        ):
            existing = CategoryService.get_category_by_name_and_type(
                updated_name,
                updated_type
            )

            if (
                existing
                and existing["category_id"] != category_id
            ):
                raise ValueError(
                    f"Category '{updated_name}' with type "
                    f"'{updated_type}' already exists."
                )

        query = """
            UPDATE categories
            SET name = %s,
                kind = %s,
                color = %s
            WHERE id = %s
        """

        execute_query(
            query,
            (
                updated_name,
                updated_type,
                updated_color,
                category_id
            ),
            commit=True
        )

        updated_category = CategoryService.get_category_by_id(
            category_id
        )

        if not updated_category:
            raise DatabaseError(
                "Category was updated but could not be retrieved."
            )

        return updated_category

    @staticmethod
    def delete_category(category_id: int) -> bool:
        """Delete a category if no transactions or budgets reference it."""

        category = CategoryService.get_category_by_id(category_id)

        if not category:
            raise KeyError(
                f"Category with ID {category_id} not found."
            )

        # Check associated transactions
        txn_check = execute_query(
            """
            SELECT COUNT(*) AS cnt
            FROM transactions
            WHERE category_id = %s
            """,
            (category_id,),
            fetch_one=True
        )

        if txn_check and txn_check["cnt"] > 0:
            raise ValueError(
                f"Cannot delete category '{category['name']}' "
                f"because {txn_check['cnt']} transaction(s) "
                "are associated with it."
            )

        # Check associated budgets
        budget_check = execute_query(
            """
            SELECT COUNT(*) AS cnt
            FROM budgets
            WHERE category_id = %s
            """,
            (category_id,),
            fetch_one=True
        )

        if budget_check and budget_check["cnt"] > 0:
            raise ValueError(
                f"Cannot delete category '{category['name']}' "
                f"because {budget_check['cnt']} budget(s) "
                "are associated with it."
            )

        execute_query(
            "DELETE FROM categories WHERE id = %s",
            (category_id,),
            commit=True
        )

        return True