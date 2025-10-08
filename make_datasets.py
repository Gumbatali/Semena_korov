import polars as pl
import os

# === Пути ===
EXCEL_PATH = "links.xlsx"
DATASET_DIR = "datasets"

print("📂 Загружаем Excel...")
df = pl.read_excel(EXCEL_PATH)

print(f"✅ Загружено {len(df)} строк, столбцы:")
print(df.columns)

# === 1️⃣ Переименовываем столбец с флагом ===
df = df.rename({
    "0 - не использовать\r\n1 - обучающая выборка\r\n2 - остальные": "split_flag"
})

# === 2️⃣ Оставляем только нужные колонки ===
columns_to_keep = [
    "Номер поля",
    "Производственное хозяйство",
    "Культура",
    "Комментарий агронома",
    "Фаза развития растения",
    "Дата создания осмотра и фотографий",
    "Идентификатор фотографии",
    "split_flag"
]
df = df.select(columns_to_keep)

# === 3️⃣ Добавляем порядковый номер (photo_index) ===
df = df.with_row_index(name="photo_index", offset=1)

# === 4️⃣ Чистим и фильтруем split_flag ===
df = (
    df
    .filter(pl.col("split_flag") != "IsUsedForAnalysis")   # убираем лишнюю строку
    .with_columns(
        pl.col("split_flag")
        .cast(pl.Utf8)
        .str.strip_chars()
        .str.replace_all(r"[^0-9]", "")
    )
)

# === 5️⃣ Проверяем уникальные значения ===
print("🔍 Уникальные значения split_flag:", df.select(pl.col("split_flag").unique()))
print("🔹 Train строк:", len(df.filter(pl.col("split_flag") == "1")))
print("🔹 Test строк:", len(df.filter(pl.col("split_flag") == "2")))

# === 6️⃣ Делим на train/test ===
train_df = df.filter(pl.col("split_flag") == "1")
test_df = df.filter(pl.col("split_flag") == "2")

# === 7️⃣ Сохраняем в Parquet ===
os.makedirs(DATASET_DIR, exist_ok=True)

train_path = os.path.join(DATASET_DIR, "train.parquet")
test_path = os.path.join(DATASET_DIR, "test.parquet")

train_df.write_parquet(train_path, compression="zstd")
test_df.write_parquet(test_path, compression="zstd")

print(f"✅ Train сохранён: {train_path} ({len(train_df)} строк)")
print(f"✅ Test сохранён:  {test_path} ({len(test_df)} строк)")

# === 8️⃣ Проверяем размер файлов ===
train_size = os.path.getsize(train_path) / 1024
test_size = os.path.getsize(test_path) / 1024
print(f"📦 Размер train.parquet: {train_size:.1f} KB")
print(f"📦 Размер test.parquet:  {test_size:.1f} KB")

# === 9️⃣ Предпросмотр ===
print("\n🪄 Первые 5 строк train_df:")
print(train_df.head(5))
