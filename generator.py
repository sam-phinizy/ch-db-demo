import polars as pl
from faker import Faker
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict
import argparse
from pathlib import Path


class EcommerceDataGenerator:
    def __init__(self, num_products: int, num_months: int, end_date: datetime = None):
        self.faker = Faker()
        self.num_products = num_products
        self.num_months = num_months
        self.end_date = end_date or datetime.now()
        self.start_date = self.end_date - timedelta(days=30 * num_months)
        self.products = self._generate_products()

    def _generate_products(self) -> List[Dict]:
        """Generate a list of product dictionaries with realistic attributes."""
        products = []
        categories = ["Electronics", "Clothing", "Home & Garden", "Books", "Sports"]

        for _ in range(self.num_products):
            product = {
                "product_id": self.faker.uuid4(),
                "name": self.faker.catch_phrase(),
                "category": self.faker.random_element(categories),
                "base_price": round(self.faker.random_number(4) / 100 + 10, 2),
                "description": self.faker.text(max_nb_chars=200),
            }
            products.append(product)
        return products

    def _generate_hourly_sales(self, date: datetime, product: Dict) -> Dict:
        """Generate realistic hourly sales data for a product."""
        # Add randomness but keep some patterns (e.g., more sales during day)
        hour = date.hour
        is_weekend = date.weekday() >= 5
        base_quantity = self.faker.random_int(0, 10)

        # More sales during business hours (9-17)
        if 9 <= hour <= 17:
            base_quantity *= 2

        # More sales on weekends
        if is_weekend:
            base_quantity = int(base_quantity * 1.5)

        # Random price fluctuation
        price_multiplier = self.faker.random_number(2) / 100 + 0.95  # 0.95 to 1.05

        return {
            "event_time": date.isoformat(),  # Added event_time
            "timestamp": date.isoformat(),  # Keeping timestamp for backward compatibility
            "product_id": product["product_id"],
            "product_name": product["name"],
            "category": product["category"],
            "quantity_sold": base_quantity,
            "unit_price": round(product["base_price"] * price_multiplier, 2),
            "total_revenue": round(
                base_quantity * product["base_price"] * price_multiplier, 2
            ),
            "weekday": date.strftime("%A"),
            "is_weekend": is_weekend,
            "hour": hour,
        }

    def generate_data(self, output_dir: str):
        """Generate and save data for the entire date range."""
        current_date = self.start_date

        while current_date <= self.end_date:
            for hour in range(24):
                current_datetime = current_date.replace(hour=hour)

                # Group products by category
                products_by_category = {}
                for product in self.products:
                    category = product["category"]
                    if category not in products_by_category:
                        products_by_category[category] = []
                    products_by_category[category].append(product)

                # Generate data for each category and product
                for category, products in products_by_category.items():
                    for product in products:
                        # Create directory structure with category
                        dir_path = (
                            Path(output_dir)
                            / str(current_datetime.year)
                            / f"{current_datetime.month:02d}"
                            / f"{current_datetime.day:02d}"
                            / f"{hour:02d}"
                            / category.lower().replace(" & ", "_and_").replace(" ", "_")
                        )

                        dir_path.mkdir(parents=True, exist_ok=True)

                        # Generate hourly data
                        sales_data = self._generate_hourly_sales(
                            current_datetime, product
                        )

                        # Use product name for the file name
                        file_name = f"{product['name'].replace(' ', '_').lower()}.json"
                        file_path = dir_path / file_name

                        with open(file_path, "w") as f:
                            json.dump(sales_data, f, indent=2)

            current_date += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(description="Generate fake e-commerce data")
    parser.add_argument(
        "--products", type=int, default=10, help="Number of products (default: 10)"
    )
    parser.add_argument(
        "--months", type=int, default=1, help="Number of months of data (default: 1)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./ecommerce_data",
        help="Output directory (default: ./ecommerce_data)",
    )

    args = parser.parse_args()

    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    generator = EcommerceDataGenerator(
        num_products=args.products, num_months=args.months, end_date=end_date
    )

    generator.generate_data(args.output_dir)


if __name__ == "__main__":
    main()
