Ketika menambahkan sumber **Harvest** di CKAN, Anda dapat menggunakan **API** atau **antarmuka pengguna (UI)**. Untuk memastikan semua field, termasuk **description** dan **configuration**, tercakup, berikut adalah penjelasan lengkap.

---

### **1. Menambahkan Sumber Harvest via API**
Anda dapat menggunakan endpoint API `harvest_source_create` untuk menambahkan sumber harvest.

#### **Endpoint**
- **URL**: `http://<ckan-instance>/api/3/action/harvest_source_create`
- **Method**: POST
- **Headers**:
  - `Authorization`: API Key admin CKAN

#### **Contoh Payload (JSON)**
```json
{
    "url": "http://example.com/catalog",
    "type": "ckan",
    "title": "Example Harvest Source",
    "description": "This is a description of the harvest source.",
    "frequency": "DAILY",
    "configuration": "{\"api_key\": \"example-api-key\", \"custom_setting\": \"value\"}",
    "owner_org": "example-org-id"
}
```

#### **Field dalam Payload**
- **`url`**: URL sumber harvest (wajib).
- **`type`**: Tipe sumber harvest, seperti:
  - `ckan`: Portal CKAN lain.
  - `csw`: Catalogue Service for the Web.
  - `waf`: Web Accessible Folder.
  - `doc`: Dokumen XML metadata individual.
- **`title`**: Nama sumber harvest yang akan ditampilkan (wajib).
- **`description`**: Penjelasan sumber harvest (opsional).
- **`frequency`**: Frekuensi harvest:
  - `MANUAL`
  - `DAILY`
  - `WEEKLY`
  - `MONTHLY`
- **`configuration`**: Pengaturan khusus dalam format JSON. Contoh:
  ```json
  {
      "api_key": "123abc",
      "custom_setting": "value"
  }
  ```
- **`owner_org`**: ID organisasi pemilik sumber harvest (opsional).

---

### **2. Menambahkan Sumber Harvest via UI**
Jika menggunakan antarmuka pengguna, ikuti langkah-langkah berikut:

#### **Langkah-Langkah:**
1. **Masuk ke CKAN**:
   - Login sebagai admin.

2. **Navigasi ke Menu Harvesting**:
   - Buka URL berikut:
     ```
     http://<ckan-instance>/harvest
     ```

3. **Klik "Add Harvest Source"**:
   - Tombol ini membawa Anda ke formulir untuk menambahkan sumber harvest.

4. **Isi Formulir**:
   - **Title**: Nama sumber harvest.
   - **URL**: Alamat URL sumber harvest.
   - **Type**: Tipe sumber harvest (`ckan`, `csw`, `waf`, dll.).
   - **Description**: Penjelasan tentang sumber harvest.
   - **Frequency**: Pilih frekuensi (`MANUAL`, `DAILY`, dll.).
   - **Configuration**:
     - Masukkan konfigurasi dalam format JSON jika dibutuhkan. Misalnya:
       ```json
       {
           "api_key": "123abc",
           "custom_param": "value"
       }
       ```

5. **Simpan**:
   - Klik tombol "Save" untuk menyimpan sumber harvest.

---

### **3. Validasi Konfigurasi**

Setelah menambahkan sumber harvest, pastikan konfigurasi berhasil:
1. Periksa sumber di UI melalui halaman **Harvest Sources**.
2. Gunakan API untuk melihat detail sumber:
   ```bash
   curl -X GET "http://<ckan-instance>/api/3/action/harvest_source_show" \
   -H "Authorization: <api-key>" \
   -d '{"id": "<source-id>"}'
   ```

Hasilnya akan menampilkan konfigurasi, deskripsi, dan pengaturan lain.

---

### **4. Contoh Response Berhasil**

Jika sumber berhasil ditambahkan, Anda akan mendapatkan respons JSON seperti ini:

```json
{
    "help": "http://<ckan-instance>/api/3/action/help_show?name=harvest_source_create",
    "success": true,
    "result": {
        "id": "1234abcd",
        "title": "Example Harvest Source",
        "url": "http://example.com/catalog",
        "type": "ckan",
        "description": "This is a description of the harvest source.",
        "frequency": "DAILY",
        "configuration": "{\"api_key\": \"example-api-key\", \"custom_setting\": \"value\"}",
        "owner_org": "example-org-id"
    }
}
```

---

Berikut adalah daftar lengkap **API CKAN Harvest** untuk melakukan operasi CRUD (Create, Read, Update, Delete) serta operasi tambahan untuk memulai atau mengelola proses harvesting.

---

### **1. API untuk Sumber Harvest**

#### **a. Create Harvest Source**
Endpoint untuk menambahkan sumber harvest baru.

- **Endpoint**: `/api/3/action/harvest_source_create`
- **Method**: POST
- **Payload Contoh**:
  ```json
  {
      "url": "http://example.com/catalog",
      "type": "ckan",
      "title": "Example Harvest Source",
      "description": "Description of the source",
      "frequency": "DAILY",
      "configuration": "{\"api_key\": \"example-api-key\"}",
      "owner_org": "example-org-id"
  }
  ```

---

#### **b. Read Harvest Source**
Endpoint untuk mengambil detail sumber harvest.

- **Endpoint**: `/api/3/action/harvest_source_show`
- **Method**: GET atau POST
- **Payload Contoh**:
  ```json
  {
      "id": "source-id"
  }
  ```

---

#### **c. Update Harvest Source**
Endpoint untuk memperbarui informasi sumber harvest.

- **Endpoint**: `/api/3/action/harvest_source_update`
- **Method**: POST
- **Payload Contoh**:
  ```json
  {
      "id": "source-id",
      "title": "Updated Harvest Source Title",
      "description": "Updated description",
      "frequency": "WEEKLY"
  }
  ```

---

#### **d. Delete Harvest Source**
Endpoint untuk menghapus sumber harvest.

- **Endpoint**: `/api/3/action/harvest_source_delete`
- **Method**: POST
- **Payload Contoh**:
  ```json
  {
      "id": "source-id"
  }
  ```

---

### **2. API untuk Pekerjaan Harvest**

#### **a. Create Harvest Job**
Endpoint untuk memulai pekerjaan harvesting pada sumber tertentu.

- **Endpoint**: `/api/3/action/harvest_job_create`
- **Method**: POST
- **Payload Contoh**:
  ```json
  {
      "source_id": "source-id"
  }
  ```

---

#### **b. List Harvest Jobs**
Endpoint untuk mengambil daftar pekerjaan harvesting.

- **Endpoint**: `/api/3/action/harvest_job_list`
- **Method**: GET atau POST
- **Payload Contoh (opsional)**:
  ```json
  {
      "source_id": "source-id"
  }
  ```

---

#### **c. Delete Harvest Job**
Endpoint untuk menghapus pekerjaan harvest tertentu.

- **Endpoint**: `/api/3/action/harvest_job_delete`
- **Method**: POST
- **Payload Contoh**:
  ```json
  {
      "id": "job-id"
  }
  ```

---

### **3. API untuk Objek Harvest**

#### **a. List Harvest Objects**
Endpoint untuk mengambil daftar objek yang dihasilkan oleh pekerjaan harvest tertentu.

- **Endpoint**: `/api/3/action/harvest_object_list`
- **Method**: GET atau POST
- **Payload Contoh**:
  ```json
  {
      "job_id": "job-id"
  }
  ```

---

#### **b. Show Harvest Object**
Endpoint untuk mengambil detail dari objek harvest tertentu.

- **Endpoint**: `/api/3/action/harvest_object_show`
- **Method**: GET atau POST
- **Payload Contoh**:
  ```json
  {
      "id": "object-id"
  }
  ```

---

#### **c. Delete Harvest Object**
Endpoint untuk menghapus objek harvest tertentu.

- **Endpoint**: `/api/3/action/harvest_object_delete`
- **Method**: POST
- **Payload Contoh**:
  ```json
  {
      "id": "object-id"
  }
  ```

---

### **4. API untuk Menjalankan atau Mengelola Harvest**

#### **a. Reimport Harvest Source**
Endpoint untuk menjalankan kembali semua pekerjaan harvest pada sumber tertentu.

- **Endpoint**: `/api/3/action/harvest_source_reimport`
- **Method**: POST
- **Payload Contoh**:
  ```json
  {
      "id": "source-id"
  }
  ```

---

#### **b. Clear Harvest Source**
Endpoint untuk menghapus semua data hasil harvest dari sumber tertentu.

- **Endpoint**: `/api/3/action/harvest_source_clear`
- **Method**: POST
- **Payload Contoh**:
  ```json
  {
      "id": "source-id"
  }
  ```

---

### **Contoh Skrip cURL untuk API Harvest**

#### a. Membuat Sumber Harvest
```bash
curl -X POST "http://<ckan-instance>/api/3/action/harvest_source_create" \
-H "Authorization: <api-key>" \
-H "Content-Type: application/json" \
-d '{
    "url": "http://example.com/catalog",
    "type": "ckan",
    "title": "Example Harvest Source",
    "description": "Description of the source",
    "frequency": "DAILY",
    "configuration": "{\"api_key\": \"example-api-key\"}",
    "owner_org": "example-org-id"
}'
```

#### b. Memulai Pekerjaan Harvest
```bash
curl -X POST "http://<ckan-instance>/api/3/action/harvest_job_create" \
-H "Authorization: <api-key>" \
-H "Content-Type: application/json" \
-d '{
    "source_id": "source-id"
}'
```

#### c. Menampilkan Status Harvest Source
```bash
curl -X GET "http://<ckan-instance>/api/3/action/harvest_source_show" \
-H "Authorization: <api-key>" \
-H "Content-Type: application/json" \
-d '{
    "id": "source-id"
}'
```

#### d. Menghapus Harvest Object
```bash
curl -X POST "http://<ckan-instance>/api/3/action/harvest_object_delete" \
-H "Authorization: <api-key>" \
-H "Content-Type: application/json" \
-d '{
    "id": "object-id"
}'
```

---

### **Kesimpulan**

Dengan API di atas, Anda dapat melakukan operasi CRUD pada sumber harvest, pekerjaan harvest, dan objek harvest. Anda juga bisa mengelola proses harvesting seperti menjalankan kembali atau membersihkan data hasil harvest.

Jika ada kebutuhan lebih spesifik atau contoh penggunaan tambahan, beri tahu saya! 😊

curl -X POST "http://localhost:5000/api/3/action/harvest_job_list" -H "Authorization: f4601f99-80fa-4090-b833-4683c64482f7"

f4601f99-80fa-4090-b833-4683c64482f7

curl -X POST "http://localhost:5000/api/3/action/harvest_job_list" \
-H "Authorization: f4601f99-80fa-4090-b833-4683c64482f7" \
-H "Content-Type: application/json" \
-d '{
    "source_id": "e5c700ec-a774-4b14-8cb1-bd6790a12169"
}'