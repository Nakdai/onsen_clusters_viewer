# onsen clusters viewer
view onsen clusters plot and summary

## 🛠 開発環境の構築 (Development Setup)
このプロジェクトはパッケージ管理に [uv](https://github.com/astral-sh/uv) を使用しています。
### 1. 前提ツール (Prerequisites)
以下のツールをインストールしてください。
- **Claude Code**
- **Cursor**
- **uv**

```zsh
curl -fsSL https://claude.ai/install.sh | bash
```
Mac (Homebrew) の場合:
```zsh
brew install uv
```
### 2. 環境セットアップ (Setup)
- リポジトリをクローン
- 依存関係をインストール
```zsh
uv sync # 仮想環境(.venv)の作成とライブラリの同期
```
これにより、`.venv` フォルダが作成され、`uv.lock` に基づいた正確なバージョンのライブラリがインストールされます。
### 3. エディタ設定 (Editor Config)
#### 🧩 推奨拡張機能のセットアップ (Setup Extensions)
このプロジェクトには、開発効率を統一するための推奨拡張機能（Python, Ruff, 日本語化など）が設定されています。
以下の手順で一括インストールしてください。
#### 手順 (GUI)
1. **拡張機能サイドバーを開く**
   - ショートカット: `Cmd + Shift + X` (Mac) / `Ctrl + Shift + X` (Win)
   - または、左側のアクティビティバーにあるテトリスのようなブロックのアイコンをクリックします。
2. **推奨事項を表示する**
   - 検索ボックスに以下の文字列を入力してください：
     ```
     @recommended
     ```
   - または、検索ボックス右横の「じょうご型アイコン (🌪️)」をクリックし、**「推奨 (Recommended)」** を選択します。
3. **一括インストール**
   - **「ワークスペースの推奨事項 (Workspace Recommendations)」** という項目が表示されます。
   - その横にある **雲のアイコン (☁️)** または **ダウンロードボタン** をクリックすると、リストにある全ての拡張機能がインストールされます。
> **Note:** プロジェクトを開いた際、右下に「このワークスペースには推奨の拡張機能があります」というポップアップが表示された場合は、そこから「インストール」をクリックするだけでも完了します。
## Git運用ルール
### 1. ブランチ戦略
```
main  -------------------------------------> (常に動作する安定版)
        \             /      \
         \-- feat/A -/        \-- feat/B ---- (作業が終わったらmainへ)
```
### 2. 命名規則
   - feat/{内容}
      - 新機能の実装・修正・docs・設定
### 3. コミット
```
<型>: <変更内容の要約（50文字以内）>
<なぜ変更したか、何が解決されるか（詳細）>
======= example =======
fix: ユーザー登録時にバリデーションエラーが発生するバグを修正
メールアドレスに大文字が含まれていると重複チェックで弾かれていたため、
保存前に小文字に変換する処理を追加。
=======================
型値
feat: 新機能
fix: バグ修正
docs: ドキュメントのみ
style: コードの動作に影響しない変更 (フォーマットなど)
refactor: リファクタリング (機能追加もバグ修正もしない)
test: テストの追加・修正
chore: その他 (ビルドツール、ライブラリ更新など)
```
### 4. コマンド
- ブランチ作成
```zsh
git switch main
git pull origin
git switch -c feat/〇〇
```
- コミット
  - 1日に1回はコミットする
```zsh
git add . # コミットすべきでないファイルがないチェックする
git commit -m "[コミットメッセージ]"
git push origin feat/〇〇
```
- マージ
  - マージはGitHub上で実施
- ブランチ削除
```zsh
git switch main
git branch -d feat/新機能名
```
## 開発

### 🛠️ 開発用コマンド (Commands)
- **ライブラリの追加**
  - `uv add [package_name]`
- **スクリプトの実行**
  - `uv run src/main.py`
- **テストの実行**
  - `uv run pytest`
- **フォーマッタ実行**
  - `uv run ruff format .`
- **Streamlit アプリの起動**
  - `uv run streamlit run <path/to/app.py> --server.headless=true`
  - ブラウザで http://localhost:8501 を開く
