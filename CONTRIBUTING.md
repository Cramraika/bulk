# Contributing to bulk

Thanks for your interest in improving **bulk** — a free, MIT-licensed utility for firing
thousands of webhooks/APIs from a CSV. Contributions are welcome.

## How to contribute

1. **Fork** the repository and create a feature branch (`git checkout -b my-change`).
2. **Make your change.** Keep it focused — one logical change per pull request.
3. **Test locally** before opening a PR (see the README for setup; `.env.example` documents config).
4. **Open a pull request** against `main` with a clear description of what and why.

## Guidelines

- Follow the existing code style (the repo uses [Ruff](https://docs.astral.sh/ruff/) for Python linting).
- Write clear commit messages ([Conventional Commits](https://www.conventionalcommits.org/) preferred).
- Never commit secrets or `.env` files — use `.env.example` as the template.
- Document any new configuration options in the README and `.env.example`.

## Reporting issues

Use the GitHub issue templates for bug reports and feature requests. Include reproduction steps,
expected vs. actual behavior, and your environment details.

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](./LICENSE).
