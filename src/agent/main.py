import argparse
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from .graph import build_graph

console = Console()


def run() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Flight Planner Agent")
    parser.add_argument(
        "--user-id",
        default=None,
        help="User ID for personalized context (e.g. user-001)",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="Base URL of the Flight Planner API",
    )
    args = parser.parse_args()

    console.print(
        Panel.fit(
            f"[bold blue]Flight Planner Agent[/bold blue]\n"
            f"Provider: [green]Azure OpenAI[/green]  |  "
            f"API: [green]{args.api_url}[/green]"
            + (f"  |  User: [green]{args.user_id}[/green]" if args.user_id else ""),
            title="✈  Welcome",
        )
    )
    console.print("[dim]Type 'exit' or press Ctrl+C to quit.[/dim]\n")

    graph = build_graph(api_base_url=args.api_url)
    history: list = []

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if user_input.strip().lower() in ("exit", "quit", "bye"):
            console.print("[dim]Goodbye![/dim]")
            break

        # Inject user context into the first message so the agent knows who it's helping.
        if args.user_id and not history:
            user_input = f"[Context: my user ID is {args.user_id}]\n{user_input}"

        history.append(HumanMessage(content=user_input))

        with console.status("[dim]Thinking…[/dim]", spinner="dots"):
            result = graph.invoke({"messages": history, "user_id": args.user_id})

        history = result["messages"]

        last_ai = next(
            (m for m in reversed(history) if isinstance(m, AIMessage) and m.content),
            None,
        )
        if last_ai:
            console.print("\n[bold green]Agent[/bold green]")
            console.print(Markdown(str(last_ai.content)))
            console.print()


if __name__ == "__main__":
    run()
