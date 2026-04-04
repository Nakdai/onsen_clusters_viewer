# CLAUDE.md

This file provides context and strict rules for Claude Code in this repository.

## 1. Project Goal
（プロジェクトの目標を記載する）

## 2. Strict Commands (AIへの強制事項)
Pythonの実行環境は `uv` で管理しています。AIが自律的にコマンドを実行する場合は、必ず以下のプレフィックスを使用してください（pipなどは使用禁止）。

- スクリプトの実行: `uv run <script_path>`
- パッケージの追加: `uv add <package>`
- フォーマット/Lint: `uv run ruff format .` / `uv run ruff check .`

## 3. Architecture & Module Boundaries
（アーキテクチャと各モジュールの責務を記載する）

## 4. Coding & Output Rules
* **Git:** コミットメッセージは `<type>: <summary>` 形式。変更理由は必ず body に含めること。
