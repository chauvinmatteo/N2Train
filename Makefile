NAME        = n2train-kanji
PYTHON      = poetry run python
SRC_DIR     = src
MAIN        = $(SRC_DIR)/main.py

GREEN       = \033[0;32m
RESET       = \033[0m

all: install run

install:
	@echo "$(GREEN)Downloading dependencies...$(RESET)"
	@poetry install

run:
	@echo "$(GREEN)Loading $(NAME)...$(RESET)"
	@$(PYTHON) $(MAIN)

test:
	@poetry run pytest

clean:
	@echo "$(GREEN)Cleaning...$(RESET)"
	@rm -rf `find . -type d -name "__pycache__"`
	@rm -rf .pytest_cache
	@rm -rf .venv

fclean: clean
	@rm -f kanji_n2.db
	@rm -f poetry.lock
	@rm -f answer_sheets.txt

re: fclean all

.PHONY: all install run test clean fclean re