![SketchRushLogo](https://github.com/NakamuraShippo/SketchRush/blob/main/image/SketchRushLogo.png)
  
[English Readme](https://github.com/NakamuraShippo/SketchRush/blob/main/Readme_EN.md)  
  
## 概要
SketchRushは、シンプルなドローツールです。  
ペンタブレットやマウスを使用して、素早くスケッチやアイデアを形にすることができます。 
30秒ドローイング、マスク、ポーズの描画等、高度な編集を要さない用途に向いています。  
[youtubeにデモ動画を上げました](https://youtu.be/DLPtTu0L4a0)  
  
## 主な機能
- フォルダ内の画像を順次表示  
- 読み込み対応形式 png gif bmp jpeg jpg webp  
- マウスを使用したドローイング  
- ペンタブレットを使用したドローイング  
- ペン色の変更  
- 背景色の変更  
- 描画内容の保存（透明背景のPNG）  
- 背景画像と結合した画像の保存  
- 保存時に自動で次の画像に遷移  
- キーボードショートカットのカスタム  
  
## インストール方法
このリポジトリをクローンまたはダウンロードします。  
Python 3.6以上がインストールされていることを確認します。  
  
解凍したフォルダ内にあるinstall_SketchRush.batをダブルクリックするとインストールを開始します。  
~~~
#手動でもインストール可能です。
python -m venv venv
pip install PyQt5 Pillow PyYAML
~~~
boot_SketchRush.batをダブルクリックすると起動します。  
~~~
#手動で起動することもできます。
venv\Scripts\Activate
py main.py
~~~
  
## 使用方法
### マウスモード  
- 左クリックで描画をできます。  
- 右クリックを押している間は消しゴムモードになります。  
- マウスホイールでペンサイズを調整できます。  
  
### ペンタブレットモード
消しゴムツールはペンタブレットの操作に準拠しています。 
それ以外の操作はマウスモードと同じです。  

### 設定
#### 基本設定
![keyboardSCR](https://github.com/NakamuraShippo/SketchRush/blob/main/image/BasicSetting.png)  
- 保存するファイル名:[:03d]と「.png」の部分は必ず保存名に含むようにしてください。(画像の例で保存されると、SketchRush001.pngとなります)  
- 背景の色:画像を読み込まない時の背景色  
- キャンバスサイズ:画像を読み込まない場合のキャンバスサイズ、幅・高さを指定  
- ペンタブレットモード:ペンタブレットの有効/無効  
- 保存時、自動的に画像を進める:保存時の処理の有効/無効  
- 言語:言語設定  
- ペンの色:「ペンの色を追加」「選択した色を削除」でペンの色を追加したり削除したりできます。各色をクリックすると設定されている色の変更ができます。  

#### キーコンフィグ
![keyboardSCR](https://github.com/NakamuraShippo/SketchRush/blob/main/image/KeyConfig.png)    
| 機能 | ショートカットキー |
|:---------------|------|
アンドゥ（Undo）| Z 
リドゥ（Redo）|	X
キャンバスのクリア |	Delete
次のペンの色	| C
前のペンの色	| V
保存 | Enter
次の画像	| → （右矢印キー）
前の画像	| ← （左矢印キー）
消しゴムツール	| E
ペンサイズを大きく | +
ペンサイズを小さく | -
結合保存（レイヤーの統合保存）| F1  

| 機能 | ショートカットキー |
|:---------------|------|
ペンツール | 左クリック
消しゴムツール(押している間有効) | 右クリック
ペンサイズを大きく | マウスホイール上回転
ペンサイズを小さく | マウスホイール下回転

## 更新履歴
2024.9.27:v1.0公開 見切り発車なのでバグがあるかも

## 今後の予定(未定)
- ComfyUI APIを経由してペイントした内容をLoad Image系のノードに送信し生成する機能  
- ツール上でプロンプトを記述しComfyUIに送信してSketchRush上で生成する機能  
  
## ライセンス
SketchRushは、著作権法により保護されています。無断での複製、改変、再配布を禁止します。  
商用利用許可しますが、使用者責任は全てツールの利用者に帰属するものとし、ツール製作者(なかむらしっぽ)はその責任を一切負わないものとします。
  
## 連絡先
バグや要望、連絡などがあればissueまたは以下のポータルからSNSやメール等からお気軽にお声掛けください。  
なかむらしっぽ / https://lit.link/nakamurashippo
