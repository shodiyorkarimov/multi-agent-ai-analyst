from src.config import settings, check_status
from src.state import new_state


def main() -> None:
    check_status()
    settings.validate_required()

    state = new_state("Bu F1 uchun sinov savoli")
    print("\nYaratilgan boshlang'ich state:")
    print(state)


if __name__ == "__main__":
    main()