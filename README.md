# ドコモ電話帳エクスポートVCF to Google連絡先インポートCSV 変換君 #
 
Python 3.6で動作確認しています。

フォーマットを独自調査し、可能な限り変換するスクリプトです。  
CSVで取り込めない項目(画像など)は無視されます。

ドコモ電話帳アプリからのエクスポートVCFには、グループ名が含まれていなかったため、  
これらの変換を希望する場合は、データコピーかドコモバックアップから電話帳をバックアップして下さい。

デフォルトで、グループ名の先頭にマイコンタクトが追加されます。  
```--no-my-contacts```をコマンドライン引数で与えると無効化することができます。

変換元の内容によっては、正しく動作・変換できない事も考えられますので、  
十分に確認してからインポートするようにして下さい。

## 必須モジュールインストール方法 ##
```bash
pip install -r requirements.txt -c constraints.txt
```

## 使い方 ##
必須モジュールインストール後、
```bash
python docomo_phonebook_vcf_to_google_csv.py (変換元VCFファイルパス) (変換先CSVファイルパス)
```
で変換することができます。
