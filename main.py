from utils import DataLoader, logger


def main():
    data_loader = DataLoader("data/20250701_y.xlsx")
    data_loader.get_sku_from_title()
    data_loader.clean_data()


if __name__ == "__main__":
    main()
