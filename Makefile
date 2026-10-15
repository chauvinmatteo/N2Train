NAME        = n2train-kanji
PYTHON      = uv run python
SRC_DIR     = src
MAIN        = $(SRC_DIR)/main.py

GREEN       = \033[0;32m
RESET       = \033[0m

all: install run

install:
	@echo "$(GREEN)Downloading dependencies...$(RESET)"
	@uv sync

run:
	@echo "$(GREEN)Loading $(NAME)...$(RESET)"
	@$(PYTHON) $(MAIN)

test:
	@uv run pytest

clean:
	@echo "$(GREEN)Cleaning...$(RESET)"
	@rm -rf `find . -type d -name "__pycache__"`
	@rm -rf .pytest_cache
	@rm -rf .venv

fclean: clean
	@rm -f uv.lock

reset: fclean
	@rm -f n2train.db

re: fclean all

.PHONY: all install run test clean fclean reset re