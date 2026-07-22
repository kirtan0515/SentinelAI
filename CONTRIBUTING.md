# Contributing

1. Fork the repo
2. Create a branch (`git checkout -b feature/my-thing`)
3. Make changes, run `make lint` and `make test`
4. Push and open a PR

## Dev setup

```bash
make up          # start postgres + redis
make migrate     # run db migrations
make test        # run pytest
make lint        # run ruff
```

## Conventions

- Backend: Python, type hints everywhere, ruff for formatting
- Frontend: TypeScript, Tailwind, functional components
- Commits: short and descriptive, no need for conventional commits format
