from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from doujinshi_meta._version import __version__
from doujinshi_meta.catalog import build_catalog
from doujinshi_meta.config import (
    UserConfig,
    clear_bika_credentials,
    credentials_path_beside,
    default_config_path,
    load_bika_credentials,
    load_config,
    mask_account,
    resolve_proxy,
    save_config,
)
from doujinshi_meta.fetch import fetch_tags
from doujinshi_meta.search import search_tags
from doujinshi_meta.search_batch import search_batch_tags
from doujinshi_meta.models import Source, TagCatalogResponse, normalize_kinds, validate_kinds_for_source

app = typer.Typer(no_args_is_help=True, add_completion=False, name="djm")
config_app = typer.Typer(no_args_is_help=True, help="持久配置")
app.add_typer(config_app, name="config")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="显示版本号并退出",
    ),
) -> None:
    """本子元数据爬取 CLI。"""


def run() -> None:
    """Console entry for ``djm``."""
    app()


class SourceOption(str, Enum):
    bika = "bika"
    jmcomic = "jmcomic"


def _write_json(data: dict, output: Path | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")


def _write_catalog_table(result: TagCatalogResponse) -> None:
    table = Table()
    table.add_column("kind")
    table.add_column("name")
    table.add_column("count", justify="right")
    for entry in result.tags:
        table.add_row(entry.kind, entry.name, str(entry.count))
    Console().print(table)


def _config_path(config: Path | None) -> Path | None:
    return config


def _effective_config_path(config: Path | None) -> Path:
    return config if config is not None else default_config_path()


def _resolved_proxy(
    proxy: Optional[str],
    no_proxy: bool,
    config_path: Path | None,
) -> str | None:
    cfg = load_config(_config_path(config_path))
    return resolve_proxy(cli_proxy=proxy, cli_no_proxy=no_proxy, config=cfg)


def _credentials_path(config_path: Path | None) -> Path:
    return credentials_path_beside(_config_path(config_path))


def _parse_ids(ids: Optional[str], ids_file: Optional[Path]) -> list[str]:
    result: list[str] = []
    if ids:
        result.extend(part.strip() for part in ids.split(",") if part.strip())
    if ids_file:
        for line in ids_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                result.append(line)
    return result


@app.command("fetch")
def fetch_cmd(
    source: SourceOption = typer.Option(..., "--source", help="来源站"),
    ids: Optional[str] = typer.Option(None, "--ids", help="逗号分隔本子 ID"),
    ids_file: Optional[Path] = typer.Option(None, "--ids-file", help="每行一个 ID"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="写入 JSON 文件"),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="单次 HTTP 代理"),
    no_proxy: bool = typer.Option(False, "--no-proxy", help="强制直连"),
    delay: Optional[float] = typer.Option(None, "--delay", help="请求间隔（秒）"),
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """单个或批量爬取漫画 tag 列表。"""
    id_list = _parse_ids(ids, ids_file)
    if not id_list:
        typer.echo("请提供 --ids 或 --ids-file", err=True)
        raise typer.Exit(code=2)

    try:
        result = fetch_tags(
            Source(source.value),
            id_list,
            proxy=_resolved_proxy(proxy, no_proxy, config),
            delay=delay,
            credentials_path=_credentials_path(config),
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    _write_json(result.to_dict(), output)
    if result.errors and not result.items:
        raise typer.Exit(code=2)
    if result.errors:
        raise typer.Exit(code=1)


@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="标题或关键词"),
    source: SourceOption = typer.Option(..., "--source", help="来源站"),
    limit: int = typer.Option(10, "--limit", min=1, help="最多拉取详情的本子数"),
    pages: Optional[int] = typer.Option(None, "--pages", min=1, help="本地页数提示，用于多命中消歧"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="写入 JSON 文件"),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="单次 HTTP 代理"),
    no_proxy: bool = typer.Option(False, "--no-proxy", help="强制直连"),
    delay: Optional[float] = typer.Option(None, "--delay", help="详情请求间隔（秒）"),
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """按标题或关键词搜索本子并爬取元数据。"""
    trimmed = query.strip()
    if not trimmed:
        typer.echo("请提供搜索关键词", err=True)
        raise typer.Exit(code=2)

    try:
        result = search_tags(
            trimmed,
            Source(source.value),
            limit=limit,
            pages=pages,
            proxy=_resolved_proxy(proxy, no_proxy, config),
            delay=delay,
            credentials_path=_credentials_path(config),
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    _write_json(result.to_dict(), output)
    if result.errors and not result.items:
        raise typer.Exit(code=2)
    if result.errors:
        raise typer.Exit(code=1)


@app.command("search-batch")
def search_batch_cmd(
    source: SourceOption = typer.Option(..., "--source", help="来源站"),
    input_path: Path = typer.Option(..., "--input", help="JSONL 输入（local_id/title/pages）"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="写入 JSON 文件"),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="单次 HTTP 代理"),
    no_proxy: bool = typer.Option(False, "--no-proxy", help="强制直连"),
    delay: Optional[float] = typer.Option(None, "--delay", help="行间详情请求间隔（秒）"),
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """批量按标题搜索本地本子并爬取元数据。"""
    try:
        result = search_batch_tags(
            input_path,
            Source(source.value),
            proxy=_resolved_proxy(proxy, no_proxy, config),
            delay=delay,
            credentials_path=_credentials_path(config),
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    _write_json(result.to_dict(), output)
    if result.items and (result.errors or result.ambiguous):
        raise typer.Exit(code=1)
    if not result.items and result.errors:
        raise typer.Exit(code=2)


@app.command("catalog")
def catalog_cmd(
    source: SourceOption = typer.Option(..., "--source", help="来源站"),
    kind: list[str] = typer.Option(
        [],
        "--kind",
        help="仅聚合/输出指定 Tag Kind（可重复）；默认全部 Kind；仍爬取全部本子详情",
    ),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="写入 JSON 文件"),
    table: bool = typer.Option(
        False,
        "--table",
        help="人类可读表格（kind/name/count）；默认 JSON 为集成契约",
    ),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="单次 HTTP 代理"),
    no_proxy: bool = typer.Option(False, "--no-proxy", help="强制直连"),
    delay: Optional[float] = typer.Option(None, "--delay", help="详情请求间隔（秒）"),
    limit: Optional[int] = typer.Option(None, "--limit", help="最多处理本子数（测试用）"),
    checkpoint: Optional[Path] = typer.Option(None, "--checkpoint", help="进度文件"),
    resume: bool = typer.Option(False, "--resume", help="从 checkpoint 续爬"),
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """全量爬取并构建 tag 词表。"""
    if table and output is not None:
        typer.echo("--table 与 -o/--output 不能同时使用", err=True)
        raise typer.Exit(code=2)

    try:
        kinds = normalize_kinds(kind or None)
        validate_kinds_for_source(Source(source.value), kinds)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    try:
        result = build_catalog(
            Source(source.value),
            proxy=_resolved_proxy(proxy, no_proxy, config),
            delay=delay,
            limit=limit,
            kinds=kinds,
            checkpoint=checkpoint,
            resume=resume,
            credentials_path=_credentials_path(config),
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    if table:
        _write_catalog_table(result)
    else:
        _write_json(result.to_dict(), output)
    if result.stats.errors and result.stats.albums_scanned == 0:
        raise typer.Exit(code=2)


@config_app.command("show")
def config_show(
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """显示当前配置。"""
    path = _effective_config_path(config)
    cfg = load_config(path)
    typer.echo(f"config: {path}")
    typer.echo(f"proxy: {cfg.proxy or '(direct)'}")
    cred_path = credentials_path_beside(path)
    stored = load_bika_credentials(cred_path)
    if stored:
        typer.echo(f"credentials: {cred_path}")
        typer.echo(f"bika_account: {mask_account(stored.account)}")
    else:
        typer.echo(f"credentials: {cred_path} (none)")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="配置项，如 proxy"),
    value: str = typer.Argument(..., help="配置值"),
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """设置持久配置。"""
    if key != "proxy":
        typer.echo(f"未知配置项: {key}", err=True)
        raise typer.Exit(code=2)
    path = _effective_config_path(config)
    save_config(UserConfig(proxy=value), path)
    typer.echo(f"已写入 {path}")


@config_app.command("unset")
def config_unset(
    key: str = typer.Argument(..., help="配置项，如 proxy 或 bika-credentials"),
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """清除持久配置。"""
    path = _effective_config_path(config)
    if key == "proxy":
        cfg = load_config(path)
        cfg.proxy = None
        save_config(cfg, path)
        typer.echo(f"已更新 {path}")
        return
    if key == "bika-credentials":
        cred_path = clear_bika_credentials(credentials_path_beside(path))
        typer.echo(f"已清除 {cred_path}")
        return
    typer.echo(f"未知配置项: {key}", err=True)
    raise typer.Exit(code=2)


if __name__ == "__main__":
    run()
