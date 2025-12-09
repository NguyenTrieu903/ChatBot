# Fix Pinecone DeprecatedPluginError

Nếu bạn gặp lỗi `pinecone.deprecated_plugins.DeprecatedPluginError` khi deploy lên Streamlit Cloud:

## Giải pháp 1: Uninstall deprecated plugins

Trong Streamlit Cloud, thêm vào `requirements.txt`:

```txt
# Uninstall deprecated plugins first
pinecone-plugin-inference==0.0.0; python_version >= "3.0"
```

Hoặc trong `packages.txt` (nếu dùng):

```txt
--uninstall pinecone-plugin-inference
```

## Giải pháp 2: Pin Pinecone version

Đảm bảo `requirements.txt` có:

```txt
pinecone>=5.0.0,<6.0.0
```

## Giải pháp 3: Set environment variable

Trong Streamlit Cloud settings, thêm environment variable:

```
PINECONE_DISABLE_DEPRECATED_PLUGIN_CHECK=1
```

## Giải pháp 4: Update code (đã được thêm vào vector_store.py)

Code đã được cập nhật để set environment variable tự động:

```python
os.environ.setdefault("PINECONE_DISABLE_DEPRECATED_PLUGIN_CHECK", "1")
```

## Kiểm tra

Sau khi deploy, kiểm tra logs để đảm bảo không còn lỗi deprecated plugin.

