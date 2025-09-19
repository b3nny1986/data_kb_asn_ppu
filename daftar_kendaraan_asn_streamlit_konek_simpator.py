import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup

st.set_page_config(layout="wide")

DATA_FILE = "hasil_pencarian.csv"
CRED_FILE = "user_cred.txt"

def format_tanggal(tanggal_str):
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            dt = datetime.strptime(str(tanggal_str), fmt)
            return dt.strftime("%d/%m/%Y")
        except Exception:
            continue
    return tanggal_str

def load_data():
    file_path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    if not os.path.exists(file_path):
        st.error(f"File {file_path} tidak ditemukan.")
        return pd.DataFrame()
    df = pd.read_csv(file_path, dtype=str)
    df['tanggal_pkb'] = df['tanggal_pkb'].apply(format_tanggal)
    df['tanggal_stnk'] = df['tanggal_stnk'].apply(format_tanggal)
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

def nopol_to_form(nopol):
    # KTVH 3745 -> KT 3745 VH
    nopol = nopol.replace(" ", "")
    if nopol.startswith("KT"):
        sisa = nopol[2:]
        nomor = ''.join([c for c in sisa if c.isdigit()])
        seri = ''.join([c for c in sisa if not c.isdigit()])
        return "KT", nomor, seri
    # fallback jika format tidak sesuai
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
    except Exception as e:
        return "", ""

def status_bayar_simpator(tg_pkb):
    # tg_pkb format: dd-mm-yyyy
    try:
        pkb_date = datetime.strptime(tg_pkb, "%d-%m-%Y")
        now = datetime.now()
        if pkb_date < now:
            return "BELUM BAYAR"
        else:
            return "MASIH HIDUP"
    except Exception:
        return "TIDAK DAPAT DITENTUKAN"

def main():
    st.title("Daftar Potensi Kendaraan Motor ASN")

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

    df = load_data()
    if df.empty:
        st.stop()

    st.subheader("Pencarian Data")
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
        nopol = detail.iloc[0]['nopol']
        st.info(f"Mengambil data PKB & STNK dari Simpator untuk nopol: {nopol}")
        tg_pkb, tg_stnk = get_simpator_info(nopol)
        status_bayar = status_bayar_simpator(tg_pkb)
        # Tampilkan detail dengan data dari Simpator
        show_df = detail[['nopol', 'alamat']].copy()
        show_df['tanggal_pkb'] = tg_pkb
        show_df['tanggal_stnk'] = tg_stnk
        show_df['status_kb'] = detail.iloc[0]['status_kb']
        show_df['status_bayar'] = status_bayar
        st.dataframe(
            show_df,
            use_container_width=True,
            height=100
        )
    else:
        st.info("Data tidak ditemukan.")

if __name__ == "__main__":
    main()