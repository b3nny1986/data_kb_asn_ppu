import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup

st.set_page_config(layout="wide")

DATA_FILE = "hasil_pencarian.csv"
CRED_FILE = "user_cred.txt"
STATUS_FILE = "status_kendaraan.csv"
TAMBAH_FILE = "data_kendaraan_baru.csv"

# Tampilkan logo di bagian atas
col_logo1, col_logo2, col_title = st.columns([1,1,6])
with col_logo1:
    st.image("logo_kaltim.png", width=80, caption="UPTD PPRD Wilayah PPU")
with col_logo2:
    st.image("logo_ppu.png", width=80, caption="Bapenda PPU")
with col_title:
    st.title("Daftar Kendaraan ASN Kabupaten PPU")

def format_tanggal(tanggal_str):
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            dt = datetime.strptime(str(tanggal_str), fmt)
            return dt.strftime("%d/%m/%Y")
        except Exception:
            continue
    return tanggal_str

def nopol_to_form(nopol):
    nopol = nopol.replace(" ", "")
    if nopol.startswith("KT"):
        sisa = nopol[2:]
        nomor = ''.join([c for c in sisa if c.isdigit()])
        seri = ''.join([c for c in sisa if not c.isdigit()])
        return "KT", nomor, seri
    return "KT", "", ""

def get_simpator_info(nopol):
    kt, nomor, seri = nopol_to_form(nopol)
    url = "http://simpator.kaltimprov.go.id/cari.php"
    payload = {
        "kt": kt,
        "nomor": nomor,
        "seri": seri,
        "pkb": "Process"
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        tg_pkb = soup.find("input", {"name": "tg_pkb"})
        tg_stnk = soup.find("input", {"name": "tg_stnk"})
        tg_pkb_val = tg_pkb["value"] if tg_pkb else ""
        tg_stnk_val = tg_stnk["value"] if tg_stnk else ""
        return tg_pkb_val, tg_stnk_val
    except Exception:
        return "", ""

def status_bayar_simpator(tg_pkb):
    try:
        pkb_date = datetime.strptime(tg_pkb, "%d-%m-%Y")
        now = datetime.now()
        if pkb_date < now:
            return "BELUM BAYAR"
        else:
            return "MASIH HIDUP"
    except Exception:
        return "TIDAK DAPAT DITENTUKAN"

def load_data():
    file_path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    if not os.path.exists(file_path):
        st.error(f"File {file_path} tidak ditemukan.")
        return pd.DataFrame()
    df = pd.read_csv(file_path, dtype=str)
    return df

def save_uploaded_file(uploaded_file):
    file_path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("Data berhasil diupdate!")

def load_cred():
    cred_path = os.path.join(os.path.dirname(__file__), CRED_FILE)
    if not os.path.exists(cred_path):
        return {"user": "admin", "pass": "04615009"}
    with open(cred_path, "r") as f:
        lines = f.readlines()
        user = lines[0].strip() if len(lines) > 0 else "admin"
        passwd = lines[1].strip() if len(lines) > 1 else "04615009"
        return {"user": user, "pass": passwd}

def save_cred(user, passwd):
    cred_path = os.path.join(os.path.dirname(__file__), CRED_FILE)
    with open(cred_path, "w") as f:
        f.write(f"{user}\n{passwd}")

def load_status_kendaraan():
    file_path = os.path.join(os.path.dirname(__file__), STATUS_FILE)
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["nopol", "nama", "alamat", "status_kendaraan", "alasan_lainnya", "tanda_tangan", "waktu_lapor"])
    df = pd.read_csv(file_path, dtype=str)
    return df

def save_status_kendaraan(df):
    file_path = os.path.join(os.path.dirname(__file__), STATUS_FILE)
    df.to_csv(file_path, index=False)

def validasi_nopol(nopol):
    import re
    pattern = r"^KT[A-Z]{1,4}\s?\d{3,4}$"
    return re.match(pattern, nopol.replace(" ", "")) is not None

def load_tambah_kendaraan():
    file_path = os.path.join(os.path.dirname(__file__), TAMBAH_FILE)
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["nama_instansi", "nopol", "nama_pegawai", "asal_kendaraan", "wilayah_terdaftar", "waktu_input"])
    df = pd.read_csv(file_path, dtype=str)
    return df

def save_tambah_kendaraan(df):
    file_path = os.path.join(os.path.dirname(__file__), TAMBAH_FILE)
    df.to_csv(file_path, index=False)

def sidebar_login():
    cred = load_cred()
    if "login" not in st.session_state:
        st.session_state.login = False
    if "user" not in st.session_state:
        st.session_state.user = cred["user"]
    if "pass" not in st.session_state:
        st.session_state.passwd = cred["pass"]

    st.sidebar.header("Login untuk Update Data")
    if not st.session_state.login:
        input_user = st.sidebar.text_input("Username")
        input_pass = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if input_user == cred["user"] and input_pass == cred["pass"]:
                st.session_state.login = True
                st.success("Login berhasil!")
            else:
                st.sidebar.error("Username atau password salah.")
    else:
        st.sidebar.success(f"Login sebagai {cred['user']}")
        if st.sidebar.button("Logout"):
            st.session_state.login = False
            st.sidebar.info("Anda telah logout.")
            st.stop()
        uploaded_file = st.sidebar.file_uploader("Upload hasil_pencarian.csv baru", type=["csv"])
        if uploaded_file is not None:
            save_uploaded_file(uploaded_file)
        st.sidebar.subheader("Ubah Username & Password")
        new_user = st.sidebar.text_input("Username baru", value=cred["user"], key="new_user")
        new_pass = st.sidebar.text_input("Password baru", value=cred["pass"], key="new_pass", type="password")
        if st.sidebar.button("Simpan Perubahan"):
            save_cred(new_user, new_pass)
            st.session_state.user = new_user
            st.session_state.passwd = new_pass
            st.sidebar.success("Username dan password berhasil diubah. Silakan login ulang.")
            st.session_state.login = False
            st.stop()

def menu_pencarian_data(df):
    st.header("Pencarian Data Kendaraan")
    col1, col2, col3 = st.columns(3)
    search_nopol = col1.text_input("Cari Nopol")
    search_nama = col2.text_input("Cari Nama")
    search_alamat = col3.text_input("Cari Alamat")

    filtered_df = df.copy()
    if search_nopol:
        filtered_df = filtered_df[filtered_df['nopol'].str.contains(search_nopol, case=False, na=False)]
    if search_nama:
        filtered_df = filtered_df[filtered_df['nama'].str.contains(search_nama, case=False, na=False)]
    if search_alamat:
        filtered_df = filtered_df[filtered_df['alamat'].str.contains(search_alamat, case=False, na=False)]

    st.dataframe(
        filtered_df[['nama_instansi', 'nopol', 'nama', 'alamat', 'tanggal_pkb', 'tanggal_stnk', 'status_kb', 'status_bayar']],
        use_container_width=True,
        height=350
    )

    st.subheader("Dashboard")
    total_data = len(df)
    st.write(f"**Total Data:** {total_data}")

    rekap = df.groupby('nama_instansi').size().reset_index(name='Jumlah Data')
    st.dataframe(rekap, use_container_width=True, height=200)

    instansi_list = sorted(df['nama_instansi'].unique())
    instansi = st.selectbox("Pilih Instansi", instansi_list)
    pegawai_list = sorted(df[df['nama_instansi'] == instansi]['nama'].unique())
    pegawai = st.selectbox("Pilih Pegawai", pegawai_list)

    st.subheader("Detail Kendaraan Pegawai")
    detail = df[(df['nama_instansi'] == instansi) & (df['nama'] == pegawai)]
    if not detail.empty:
        detail_pkb = []
        detail_stnk = []
        detail_status_bayar = []
        for nopol in detail['nopol']:
            tg_pkb, tg_stnk = get_simpator_info(nopol)
            detail_pkb.append(tg_pkb)
            detail_stnk.append(tg_stnk)
            detail_status_bayar.append(status_bayar_simpator(tg_pkb))
        show_df = detail[['nopol', 'alamat']].copy()
        show_df['tanggal_pkb'] = detail_pkb
        show_df['tanggal_stnk'] = detail_stnk
        show_df['status_kb'] = detail['status_kb']
        show_df['status_bayar'] = detail_status_bayar
        st.dataframe(
            show_df,
            use_container_width=True,
            height=210
        )
    else:
        st.info("Data tidak ditemukan.")

def menu_laporan_status(df):
    st.header("Laporan Status Kendaraan")
    status_opsi = ["DIJUAL", "RUSAK", "HILANG", "DITARIK LEASING", "ALASAN LAINNYA"]

    # Gunakan session_state untuk alasan lainnya agar tetap tampil dinamis
    if "status_kendaraan" not in st.session_state:
        st.session_state.status_kendaraan = status_opsi[0]
    if "alasan_lainnya" not in st.session_state:
        st.session_state.alasan_lainnya = ""

    with st.form("form_status_kendaraan"):
        nopol_lapor = st.text_input("Nomor Polisi (Contoh: KTVV 1234, KTV 1234, KTVVV1234)")
        nama_lapor = ""
        alamat_lapor = ""
        error_nopol = False
        nopol_terdaftar = False

        if nopol_lapor:
            if not validasi_nopol(nopol_lapor):
                st.error("MOHON MASUKKAN NOPOL SESUAI FORMAT")
                error_nopol = True
            else:
                df_nopol = df[df['nopol'].str.replace(" ", "") == nopol_lapor.replace(" ", "")]
                if not df_nopol.empty:
                    nama_lapor = df_nopol.iloc[0]['nama']
                    alamat_lapor = df_nopol.iloc[0]['alamat']
                    nopol_terdaftar = True
                    st.info(f"Nama: {nama_lapor}\nAlamat: {alamat_lapor}")
                else:
                    st.warning("Nopol tidak ditemukan di data sistem.")
        else:
            st.warning("Silahkan mengisi nopol.")

        status_kendaraan = st.selectbox(
            "Status Kendaraan", status_opsi, 
            index=status_opsi.index(st.session_state.status_kendaraan) if st.session_state.status_kendaraan in status_opsi else 0,
            key="status_kendaraan"
        )

        if st.session_state.status_kendaraan == "ALASAN LAINNYA":
            alasan_lainnya = st.text_input("Isi Alasan Lainnya", key="alasan_lainnya")
        else:
            alasan_lainnya = ""

        tanda_tangan = st.text_input("Tanda Tangan (Nama Pelapor)")
        submit = st.form_submit_button("Laporkan Status Kendaraan")

        if submit:
            if not nopol_lapor:
                st.error("Silahkan mengisi nopol.")
            elif error_nopol:
                st.error("MOHON MASUKKAN NOPOL SESUAI FORMAT")
            elif not nopol_terdaftar:
                st.error("Masukkan nopol yang terdaftar dalam sistem.")
            else:
                waktu_lapor = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                df_status = load_status_kendaraan()
                new_row = {
                    "nopol": nopol_lapor,
                    "nama": nama_lapor,
                    "alamat": alamat_lapor,
                    "status_kendaraan": st.session_state.status_kendaraan,
                    "alasan_lainnya": st.session_state.alasan_lainnya if st.session_state.status_kendaraan == "ALASAN LAINNYA" else "",
                    "tanda_tangan": tanda_tangan,
                    "waktu_lapor": waktu_lapor
                }
                df_status = pd.concat([df_status, pd.DataFrame([new_row])], ignore_index=True)
                save_status_kendaraan(df_status)
                st.success("Laporan status kendaraan berhasil disimpan!")

    st.subheader("Download & Rekap Laporan Status Kendaraan")
    df_status = load_status_kendaraan()
    if not df_status.empty:
        st.download_button(
            label="Download status_kendaraan.csv",
            data=df_status.to_csv(index=False).encode("utf-8"),
            file_name="status_kendaraan.csv",
            mime="text/csv"
        )
        rekap_status = df_status.groupby('status_kendaraan').size().reset_index(name='Jumlah Laporan')
        st.dataframe(rekap_status, use_container_width=True, height=200)
        st.dataframe(df_status, use_container_width=True, height=250)
    else:
        st.info("Belum ada laporan status kendaraan.")

def menu_tambah_kendaraan(df):
    st.header("Tambah Data Kendaraan Bermotor")
    df_tambah = load_tambah_kendaraan()
    instansi_list = sorted(df['nama_instansi'].unique())

    # Daftar kabupaten di Kalimantan Timur
    kabupaten_kaltim = [
        "Berau", "Kutai Barat", "Kutai Kartanegara", "Kutai Timur", "Paser",
        "Penajam Paser Utara", "Balikpapan", "Bontang", "Samarinda", "Mahakam Ulu"
    ]
    # Daftar provinsi di Indonesia
    provinsi_indonesia = [
        "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau", "Jambi", "Sumatera Selatan", "Bangka Belitung",
        "Bengkulu", "Lampung", "DKI Jakarta", "Jawa Barat", "Banten", "Jawa Tengah", "DI Yogyakarta", "Jawa Timur",
        "Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan",
        "Kalimantan Timur", "Kalimantan Utara", "Sulawesi Utara", "Gorontalo", "Sulawesi Tengah", "Sulawesi Barat",
        "Sulawesi Selatan", "Sulawesi Tenggara", "Maluku", "Maluku Utara", "Papua", "Papua Barat", "Papua Tengah",
        "Papua Pegunungan", "Papua Selatan", "Papua Barat Daya"
    ]

    nama_instansi = st.selectbox("Nama Instansi", instansi_list)
    nopol = st.text_input("Nomor Polisi")
    nama_pegawai = st.text_input("Nama Pegawai")
    asal_kendaraan = st.selectbox("Asal Kendaraan", ["KT", "Non KT"])

    wilayah_terdaftar = ""
    if asal_kendaraan == "KT":
        st.caption("Masukkan nama Kabupaten apabila masih dalam wilayah KT (Kalimantan Timur)")
        wilayah_terdaftar = st.selectbox("Wilayah Asal Terdaftar", kabupaten_kaltim)
    else:
        st.caption("Masukkan nama Provinsi apabila diluar wilayah KT / Non KT")
        wilayah_terdaftar = st.selectbox("Wilayah Asal Terdaftar", provinsi_indonesia)

    submit = st.button("Tambah Data Kendaraan")

    if submit:
        if not nama_instansi or not nopol or not nama_pegawai or not asal_kendaraan or not wilayah_terdaftar:
            st.error("Semua kolom wajib diisi!")
        else:
            waktu_input = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            new_row = {
                "nama_instansi": nama_instansi,
                "nopol": nopol,
                "nama_pegawai": nama_pegawai,
                "asal_kendaraan": asal_kendaraan,
                "wilayah_terdaftar": wilayah_terdaftar,
                "waktu_input": waktu_input
            }
            if "wilayah_terdaftar" not in df_tambah.columns:
                df_tambah["wilayah_terdaftar"] = ""
            df_tambah = pd.concat([df_tambah, pd.DataFrame([new_row])], ignore_index=True)
            save_tambah_kendaraan(df_tambah)
            st.success("Data kendaraan berhasil ditambahkan!")

    st.subheader("Rekap Data Kendaraan Baru")
    if not df_tambah.empty:
        rekap = df_tambah.groupby('asal_kendaraan').size().reset_index(name='Jumlah')
        st.dataframe(rekap, use_container_width=True, height=120)
        st.subheader("Rincian Data Kendaraan Baru")
        st.dataframe(df_tambah, use_container_width=True, height=250)
        st.download_button(
            label="Download Data Kendaraan Baru (CSV)",
            data=df_tambah.to_csv(index=False).encode("utf-8"),
            file_name="data_kendaraan_baru.csv",
            mime="text/csv"
        )
    else:
        st.info("Belum ada data kendaraan baru yang ditambahkan.")

def main():
    sidebar_login()

    menu = st.sidebar.radio(
        "Menu Utama",
        ("Pencarian Data Kendaraan", "Laporan Status Kendaraan", "Tambah Data Kendaraan"),
        index=0
    )

    df = load_data()
    if df.empty:
        st.stop()

    if menu == "Pencarian Data Kendaraan":
        menu_pencarian_data(df)
    elif menu == "Laporan Status Kendaraan":
        menu_laporan_status(df)
    elif menu == "Tambah Data Kendaraan":
        menu_tambah_kendaraan(df)

    # Help Desk menu dengan icon WhatsApp
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Help Desk**")
    st.sidebar.markdown(
        """
        <a href="https://wa.me/6285346009498" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="25" style="vertical-align:middle;margin-right:8px;">
            WhatsApp Help Desk
        </a>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()