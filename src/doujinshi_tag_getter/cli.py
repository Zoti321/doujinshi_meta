from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from doujinshi_tag_getter.catalog import build_catalog
from doujinshi_tag_getter.config import (
    DEFAULT_CONFIG_PATH,
    UserConfig,
    load_config,
    resolve_proxy,
    save_config,
)
from doujinshi_tag_getter.fetch import fetch_tags
from doujinshi_tag_getter.models import Source

app = typer.Typer(no_args_is_help=True, add_completion=False, name="dtg")
config_app = typer.Typer(no_args_is_help=True, help="持久配置")
app.add_typer(config_app, name="config")


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


def _config_path(config: Path | None) -> Path | None:
    return config


def _resolved_proxy(
    proxy: Optional[str],
    no_proxy: bool,
    config_path: Path | None,
) -> str | None:
    cfg = load_config(_config_path(config_path))
    return resolve_proxy(cli_proxy=proxy, cli_no_proxy=no_proxy, config=cfg)


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
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    _write_json(result.to_dict(), output)
    if result.errors and not result.items:
        raise typer.Exit(code=2)
    if result.errors:
        raise typer.Exit(code=1)


@app.command("catalog")
def catalog_cmd(
    source: SourceOption = typer.Option(..., "--source", help="来源站"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="写入 JSON 文件"),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="单次 HTTP 代理"),
    no_proxy: bool = typer.Option(False, "--no-proxy", help="强制直连"),
    delay: Optional[float] = typer.Option(None, "--delay", help="详情请求间隔（秒）"),
    limit: Optional[int] = typer.Option(None, "--limit", help="最多处理本子数（测试用）"),
    checkpoint: Optional[Path] = typer.Option(None, "--checkpoint", help="进度文件"),
    resume: bool = typer.Option(False, "--resume", help="从 checkpoint 续爬"),
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """全量爬取并构建 tag 词表。"""
    try:
        result = build_catalog(
            Source(source.value),
            proxy=_resolved_proxy(proxy, no_proxy, config),
            delay=delay,
            limit=limit,
            checkpoint=checkpoint,
            resume=resume,
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    _write_json(result.to_dict(), output)
    if result.stats.errors and result.stats.albums_scanned == 0:
        raise typer.Exit(code=2)


@config_app.command("show")
def config_show(
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """显示当前配置。"""
    path = _config_path(config) or DEFAULT_CONFIG_PATH
    cfg = load_config(path)
    typer.echo(f"config: {path}")
    typer.echo(f"proxy: {cfg.proxy or '(direct)'}")


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
    path = _config_path(config) or DEFAULT_CONFIG_PATH
    save_config(UserConfig(proxy=value), path)
    typer.echo(f"已写入 {path}")


@config_app.command("unset")
def config_unset(
    key: str = typer.Argument(..., help="配置项，如 proxy"),
    config: Optional[Path] = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """清除持久配置。"""
    if key != "proxy":
        typer.echo(f"未知配置项: {key}", err=True)
        raise typer.Exit(code=2)
    path = _config_path(config) or DEFAULT_CONFIG_PATH
    cfg = load_config(path)
    cfg.proxy = None
    save_config(cfg, path)
    typer.echo(f"已更新 {path}")


if __name__ == "__main__":
    app()
