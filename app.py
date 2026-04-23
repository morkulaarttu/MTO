# -*- coding: utf-8 -*-

# MTO — Mp3ToOgg
# Copyright © 2026 @MorkulaArttu. All rights reserved.
# Licensed under GNU GPL v3 — see LICENSE for details
# https://github.com/morkulaarttu/MTO
#
# MTO is a free Windows tool for My Winter Car players.
# It converts MP3 files to OGG format and downloads YouTube audio
# directly into the game's Radio folder.

"""
MP3 → OGG Converter + YouTube Downloader
Build: python -m PyInstaller --onefile --windowed --name "MTO" --clean app.py
"""

import os, subprocess, threading, zipfile, urllib.request, shutil, time, json, re
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog


def notify(title: str, message: str):
    """Show a Windows toast notification using PowerShell — no extra libraries."""
    try:
        title   = title.replace("'", "''")
        message = message.replace("'", "''")
        script = (
            f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null;"
            f"[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null;"
            f"$template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02;"
            f"$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template);"
            f"$xml.GetElementsByTagName('text')[0].AppendChild($xml.CreateTextNode('{title}')) | Out-Null;"
            f"$xml.GetElementsByTagName('text')[1].AppendChild($xml.CreateTextNode('{message}')) | Out-Null;"
            f"$notif = [Windows.UI.Notifications.ToastNotification]::new($xml);"
            f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('MP3toOGG').Show($notif);"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", script],
            creationflags=NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

ctk.set_default_color_theme("dark-blue")

NO_WINDOW   = 0x08000000

import logging
from logging.handlers import RotatingFileHandler

def _setup_logging():
    log_dir  = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "MP3toOGG", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "MTO.log")
    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_h = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_h.setFormatter(fmt); file_h.setLevel(logging.DEBUG)
    con_h  = logging.StreamHandler()
    con_h.setFormatter(fmt);  con_h.setLevel(logging.DEBUG)
    logger = logging.getLogger("MTO")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_h)
    logger.addHandler(con_h)
    logger.info("MTO logger initialized")
    return logger

log = logging.getLogger("MTO")
APP_DIR     = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "MP3toOGG")
BIN_DIR     = os.path.join(APP_DIR, "bin")
FFMPEG      = os.path.join(BIN_DIR, "ffmpeg.exe")
YTDLP       = os.path.join(BIN_DIR, "yt-dlp.exe")
CONFIG_FILE  = os.path.join(APP_DIR, "config.json")
APP_VERSION  = "1.1.0-beta"
_APP_INSTANCE = None
GITHUB_API   = "https://api.github.com/repos/morkulaarttu/MTO/releases/latest"
FFMPEG_URL  = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
YTDLP_URL   = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

THEMES = {
    "dark": {
        "bg":       "#0c0c1a", "surface":  "#14142a", "surface2": "#1c1c3a",
        "surface3": "#242450", "border":   "#303060", "border_hi":"#6060c0",
        "accent":   "#7b68ee", "acc_hi":   "#9d8fff", "acc_dim":  "#5040c0",
        "text":     "#ffffff", "subtext":  "#aaaacc", "muted":    "#28284a",
        "success":  "#40d98a", "error":    "#ff4466", "warning":  "#ffaa33",
        "btn_bg":   "#1e1e48", "btn_hi":   "#2a2a60", "btn_pr":   "#14143a",
        "btn_bdr":  "#5050a0", "btn_bdr_h":"#8888cc", "btn_txt":  "#ffffff",
        "abtn_bg":  "#4030a0", "abtn_hi":  "#5a44c0", "abtn_pr":  "#30208a",
        "abtn_bdr": "#7060d8", "abtn_bdh": "#a090ff", "abtn_txt": "#ffffff",
        "dbtn_bg":  "#600020", "dbtn_hi":  "#880033", "dbtn_pr":  "#440018",
        "dbtn_bdr": "#cc2244", "dbtn_bdh": "#ff5577", "dbtn_txt": "#ffffff",
    },
    "light": {
        "bg":       "#f0f0fc", "surface":  "#ffffff", "surface2": "#f0f0ff",
        "surface3": "#e4e4f8", "border":   "#d0d0ee", "border_hi":"#a0a0dd",
        "accent":   "#6050d8", "acc_hi":   "#8070f0", "acc_dim":  "#4030b0",
        "text":     "#0a0a2a", "subtext":  "#404070", "muted":    "#d8d8ee",
        "success":  "#00a060", "error":    "#cc0033", "warning":  "#cc7700",
        "btn_bg":   "#e8e8ff", "btn_hi":   "#dcdcff", "btn_pr":   "#d0d0f8",
        "btn_bdr":  "#b0b0e0", "btn_bdr_h":"#8080cc", "btn_txt":  "#0a0a2a",
        "abtn_bg":  "#6050d8", "abtn_hi":  "#7060e8", "abtn_pr":  "#5040c8",
        "abtn_bdr": "#8070f0", "abtn_bdh": "#a090ff", "abtn_txt": "#ffffff",
        "dbtn_bg":  "#cc0033", "dbtn_hi":  "#dd1144", "dbtn_pr":  "#aa0022",
        "dbtn_bdr": "#ee2255", "dbtn_bdh": "#ff4466", "dbtn_txt": "#ffffff",
    }
}

_theme = "dark"

def TH(k): return THEMES[_theme].get(k, "#ff00ff")

def apply_theme(name, accent=None):
    global _theme; _theme = name
    ctk.set_appearance_mode("dark" if name == "dark" else "light")
    if accent:
        try:
            import colorsys
            r,g,b = int(accent[1:3],16)/255, int(accent[3:5],16)/255, int(accent[5:7],16)/255
            h,s,v = colorsys.rgb_to_hsv(r,g,b)
            dim = colorsys.hsv_to_rgb(h, s, max(0, v-0.2))
            hi  = colorsys.hsv_to_rgb(h, max(0, s-0.15), min(1, v+0.15))
            dim_hex = "#{:02x}{:02x}{:02x}".format(int(dim[0]*255),int(dim[1]*255),int(dim[2]*255))
            hi_hex  = "#{:02x}{:02x}{:02x}".format(int(hi[0]*255),int(hi[1]*255),int(hi[2]*255))
            THEMES[name]["accent"]   = accent
            THEMES[name]["acc_hi"]   = hi_hex
            THEMES[name]["acc_dim"]  = dim_hex
            THEMES[name]["abtn_bg"]  = dim_hex
            THEMES[name]["abtn_hi"]  = accent
            THEMES[name]["abtn_bdh"] = hi_hex
        except: pass

def hex_lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    try:
        r1,g1,b1 = int(c1[1:3],16),int(c1[3:5],16),int(c1[5:7],16)
        r2,g2,b2 = int(c2[1:3],16),int(c2[3:5],16),int(c2[5:7],16)
        return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"
    except: return c1

class AnimBtn(ctk.CTkButton):
    """
    CTkButton subclass with smooth hover animation + glass-style border highlight.
    variant: "normal" | "accent" | "danger"
    """
    def __init__(self, master, variant="normal", anim_speed=0.14, **kw):
        self._variant = variant
        self._anim_t  = 0.0
        self._anim_dir= 0
        self._aid     = None
        self._update_variant_colors()
        kw.setdefault("corner_radius", 10)
        kw.setdefault("border_width",  2)
        kw.setdefault("fg_color",      self._c_base)
        kw.setdefault("hover_color",   self._c_hover)
        kw.setdefault("border_color",  self._c_bdr)
        kw.setdefault("text_color",    self._c_txt)
        kw.setdefault("font",          ("Segoe UI", 12, "bold"))
        super().__init__(master, **kw)
        self._speed = anim_speed
        self.bind("<Enter>", self._enter, add="+")
        self.bind("<Leave>", self._leave, add="+")

    def _update_variant_colors(self):
        v = self._variant
        if v == "accent":
            self._c_base  = TH("abtn_bg");  self._c_hover = TH("abtn_hi")
            self._c_press = TH("abtn_pr");  self._c_bdr   = TH("abtn_bdr")
            self._c_bdr_h = TH("abtn_bdh"); self._c_txt   = TH("abtn_txt")
        elif v == "danger":
            self._c_base  = TH("dbtn_bg");  self._c_hover = TH("dbtn_hi")
            self._c_press = TH("dbtn_pr");  self._c_bdr   = TH("dbtn_bdr")
            self._c_bdr_h = TH("dbtn_bdh"); self._c_txt   = TH("dbtn_txt")
        else:
            self._c_base  = TH("btn_bg");   self._c_hover = TH("btn_hi")
            self._c_press = TH("btn_pr");   self._c_bdr   = TH("btn_bdr")
            self._c_bdr_h = TH("btn_bdr_h");self._c_txt   = TH("btn_txt")

    def reapply_theme(self):
        self._update_variant_colors()
        try:
            self.configure(
                fg_color=self._c_base, hover_color=self._c_hover,
                border_color=self._c_bdr, text_color=self._c_txt)
        except: pass
        self._anim_t = 0.0

    def _cancel(self):
        if self._aid:
            try: self.after_cancel(self._aid)
            except: pass
            self._aid = None

    def _tick(self):
        self._anim_t = max(0.0, min(1.0, self._anim_t + self._anim_dir * self._speed))
        try:
            self.configure(
                fg_color=hex_lerp(self._c_base, self._c_hover, self._anim_t),
                border_color=hex_lerp(self._c_bdr, self._c_bdr_h, self._anim_t))
        except: pass
        if 0.0 < self._anim_t < 1.0:
            self._aid = self.after(14, self._tick)

    def _enter(self, _):
        self._cancel(); self._anim_dir = 1; self._tick()

    def _leave(self, _):
        self._cancel(); self._anim_dir = -1; self._tick()

_lang = "en"

STRINGS = {
"app_sub":      {"fi":"Mp3ToOgg — Audio Converter + YouTube Downloader","en":"Mp3ToOgg — Audio Converter + YouTube Downloader","sv":"Konverterare + Nedladdare","de":"Konverter + Downloader","fr":"Convertisseur + Téléchargeur","es":"Conversor + Descargador","zh":"转换器 + YouTube下载","ja":"コンバーター","ko":"변환기 + 다운로더"},
"setup_title":  {"fi":"Ensimmäinen käynnistys","en":"First Launch","sv":"Första start","de":"Erster Start","fr":"Premier démarrage","es":"Primer inicio","zh":"首次启动","ja":"初回起動","ko":"첫 실행"},
"setup_body":   {"fi":"Ladataan kaksi työkalua GitHubista\nautomaattisesti käyttäjätilillesi.","en":"Two tools will be downloaded from\nGitHub automatically for your account.","sv":"Två verktyg laddas ned automatiskt från GitHub.","de":"Zwei Tools werden automatisch von GitHub geladen.","fr":"Deux outils seront téléchargés depuis GitHub.","es":"Dos herramientas se descargarán de GitHub.","zh":"将从 GitHub 自动下载两个工具。","ja":"2つのツールをGitHubから自動DLします。","ko":"두 도구를 GitHub에서 자동 다운로드합니다."},
"install_dir":  {"fi":"ASENNUSKANSIO","en":"INSTALL PATH","sv":"INSTALLATIONSMAPP","de":"INSTALLATIONSORDNER","fr":"CHEMIN D'INSTALLATION","es":"RUTA DE INSTALACIÓN","zh":"安装路径","ja":"インストール先","ko":"설치 경로"},
"btn_install":  {"fi":"Asenna ja jatka","en":"Install & Continue","sv":"Installera & fortsätt","de":"Installieren","fr":"Installer","es":"Instalar","zh":"安装","ja":"インストール","ko":"설치"},
"btn_ing":      {"fi":"Asennetaan...","en":"Installing...","sv":"Installerar...","de":"Installiere...","fr":"Installation...","es":"Instalando...","zh":"安装中...","ja":"インストール中...","ko":"설치 중..."},
"btn_retry":    {"fi":"Yritä uudelleen","en":"Retry","sv":"Försök igen","de":"Wiederholen","fr":"Réessayer","es":"Reintentar","zh":"重试","ja":"再試行","ko":"다시 시도"},
"done_install": {"fi":"Asennus valmis!","en":"Installation complete!","sv":"Klart!","de":"Fertig!","fr":"Terminé!","es":"¡Listo!","zh":"完成！","ja":"完了！","ko":"완료!"},
"once":         {"fi":"Tapahtuu vain kerran.","en":"Happens only once.","sv":"Sker bara en gång.","de":"Nur einmal.","fr":"Une seule fois.","es":"Solo una vez.","zh":"仅一次。","ja":"一度だけ。","ko":"한 번만."},
"ffmpeg_d":     {"fi":"Audio-konversio  (BtbN @ GitHub)","en":"Audio conversion  (BtbN @ GitHub)","sv":"Ljudkonvertering","de":"Audiokonvertierung","fr":"Conversion audio","es":"Conversión audio","zh":"音频转换","ja":"音声変換","ko":"오디오 변환"},
"ytdlp_d":      {"fi":"YouTube-lataus  (yt-dlp @ GitHub)","en":"YouTube download  (yt-dlp @ GitHub)","sv":"YouTube-nedladdning","de":"YouTube-Download","fr":"Téléch. YouTube","es":"Descarga YouTube","zh":"YouTube下载","ja":"YTダウンロード","ko":"유튜브 다운로드"},
"src_lbl":      {"fi":"LÄHDE","en":"SOURCE FOLDER","sv":"KÄLLMAPP","de":"QUELLORDNER","fr":"DOSSIER SOURCE","es":"ORIGEN","zh":"源文件夹","ja":"ソースフォルダ","ko":"소스 폴더"},
"dst_lbl":      {"fi":"KOHDEKANSIO","en":"DESTINATION","sv":"MÅLMAPP","de":"ZIELORDNER","fr":"DESTINATION","es":"DESTINO","zh":"目标文件夹","ja":"保存先","ko":"대상 폴더"},
"browse":       {"fi":"Selaa","en":"Browse","sv":"Bläddra","de":"Suchen","fr":"Parcourir","es":"Explorar","zh":"浏览","ja":"参照","ko":"찾아보기"},
"files_lbl":    {"fi":"TIEDOSTOT","en":"FILES","sv":"FILER","de":"DATEIEN","fr":"FICHIERS","es":"ARCHIVOS","zh":"文件","ja":"ファイル","ko":"파일"},
"s_found":      {"fi":"MP3 löydetty","en":"MP3 found","sv":"MP3 hittade","de":"MP3 gefunden","fr":"MP3 trouvés","es":"MP3 hallados","zh":"找到 MP3","ja":"MP3検出","ko":"MP3 발견"},
"s_exists":     {"fi":"OGG olemassa","en":"OGG existing","sv":"OGG finns","de":"OGG vorhanden","fr":"OGG existants","es":"OGG existentes","zh":"已有 OGG","ja":"既存OGG","ko":"기존 OGG"},
"s_next":       {"fi":"Seuraava #","en":"Next #","sv":"Nästa #","de":"Nächste #","fr":"Prochain #","es":"Siguiente #","zh":"下一个","ja":"次","ko":"다음"},
"s_free":       {"fi":"Vapaita","en":"Free slots","sv":"Lediga","de":"Frei","fr":"Libres","es":"Libres","zh":"可用","ja":"空き","ko":"여유"},
"btn_start":    {"fi":"Käynnistä konvertointi","en":"Start Conversion","sv":"Starta","de":"Starten","fr":"Lancer","es":"Iniciar","zh":"开始转换","ja":"変換開始","ko":"변환 시작"},
"btn_conv":     {"fi":"Konvertoidaan...","en":"Converting...","sv":"Konverterar...","de":"Konvertiere...","fr":"Conversion...","es":"Convirtiendo...","zh":"转换中...","ja":"変換中...","ko":"변환 중..."},
"ready":        {"fi":"Valmis","en":"Ready","sv":"Klar","de":"Bereit","fr":"Prêt","es":"Listo","zh":"就绪","ja":"準備完了","ko":"준비"},
"done_all":     {"fi":"Kaikki {n} konvertoitu!","en":"All {n} converted!","sv":"Alla {n} klara!","de":"Alle {n} fertig!","fr":"Tous convertis !","es":"¡Todos convertidos!","zh":"全部完成！","ja":"完了！","ko":"완료!"},
"done_part":    {"fi":"{ok} ok, {err} epäonnistui","en":"{ok} ok, {err} failed","sv":"{ok} ok, {err} fel","de":"{ok} ok, {err} Fehler","fr":"{ok} ok, {err} échoués","es":"{ok} ok, {err} errores","zh":"{ok}成功 {err}失败","ja":"{ok}成功 {err}失敗","ko":"{ok}성공 {err}실패"},
"empty":        {"fi":"Valitse kansio","en":"Select a folder","sv":"Välj en mapp","de":"Ordner wählen","fr":"Choisir un dossier","es":"Selecciona carpeta","zh":"选择文件夹","ja":"フォルダを選択","ko":"폴더 선택"},
"no_mp3":       {"fi":"Ei MP3-tiedostoja","en":"No MP3 files found","sv":"Inga MP3-filer","de":"Keine MP3-Dateien","fr":"Aucun MP3","es":"No hay MP3","zh":"没有 MP3","ja":"MP3なし","ko":"MP3 없음"},
"max":          {"fi":"Max 200 trackia saavutettu.","en":"Max 200 tracks reached.","sv":"Max 200.","de":"Max. 200.","fr":"Max 200.","es":"Máx. 200.","zh":"达200上限。","ja":"最大200。","ko":"최대 200."},
"all_used":     {"fi":"Kaikki 1–200 käytössä.","en":"All 1–200 in use.","sv":"Alla 1–200.","de":"Alle vergeben.","fr":"Tous utilisés.","es":"Todos en uso.","zh":"全部使用。","ja":"1-200すべて使用。","ko":"모두 사용 중."},
"url_lbl":      {"fi":"YOUTUBE URL","en":"YOUTUBE URL","sv":"YOUTUBE URL","de":"YOUTUBE URL","fr":"URL YOUTUBE","es":"URL YOUTUBE","zh":"YouTube 链接","ja":"YouTube URL","ko":"YouTube URL"},
"sw_video":     {"fi":"Vain video","en":"Single video","sv":"Bara video","de":"Nur Video","fr":"Vidéo seule","es":"Solo vídeo","zh":"单个视频","ja":"単一動画","ko":"단일 동영상"},
"sw_playlist":  {"fi":"Koko playlist","en":"Full playlist","sv":"Hela listan","de":"Ganze Playlist","fr":"Playlist entière","es":"Lista completa","zh":"完整列表","ja":"全プレイリスト","ko":"전체 재생목록"},
"btn_dl":       {"fi":"Lataa","en":"Download","sv":"Ladda ner","de":"Herunterladen","fr":"Télécharger","es":"Descargar","zh":"下载","ja":"DL","ko":"다운로드"},
"btn_dling":    {"fi":"Ladataan...","en":"Downloading...","sv":"Laddar...","de":"Lade...","fr":"Téléchargement...","es":"Descargando...","zh":"下载中...","ja":"DL中...","ko":"다운 중..."},
"btn_stop":     {"fi":"Pysäytä","en":"Stop","sv":"Stoppa","de":"Stopp","fr":"Arrêter","es":"Detener","zh":"停止","ja":"停止","ko":"중지"},
"stopped":      {"fi":"Pysäytetty.","en":"Stopped.","sv":"Stoppad.","de":"Gestoppt.","fr":"Arrêté.","es":"Detenido.","zh":"已停止。","ja":"停止。","ko":"중지됨."},
"log_hint":     {"fi":"Liitä YouTube-linkki ja valitse kansio.\nTiedostot nimetään automaattisesti trackX.ogg.\n","en":"Paste a YouTube link and choose a folder.\nFiles are named automatically as trackX.ogg.\n","sv":"Klistra in länk och välj mapp.\nFiler namnges automatiskt trackX.ogg.\n","de":"Link und Ordner wählen. Dateien: trackX.ogg.\n","fr":"Lien + dossier. Fichiers: trackX.ogg.\n","es":"Enlace + carpeta. Archivos: trackX.ogg.\n","zh":"粘贴链接并选择文件夹。文件命名为 trackX.ogg。\n","ja":"リンク貼り付けフォルダ選択。trackX.ogg自動命名。\n","ko":"링크+폴더. 파일: trackX.ogg.\n"},
"no_url":       {"fi":"Anna URL ensin.","en":"Enter a URL first.","sv":"Ange URL.","de":"URL eingeben.","fr":"Entrez URL.","es":"Ingresa URL.","zh":"请输入链接。","ja":"URLを入力。","ko":"URL 입력."},
"no_folder":    {"fi":"Valitse kohdekansio ensin.","en":"Select a destination folder first.","sv":"Välj mapp.","de":"Ordner wählen.","fr":"Choisir dossier.","es":"Selecciona carpeta.","zh":"选择文件夹。","ja":"フォルダ選択。","ko":"폴더 선택."},
"el":           {"fi":"Kulunut","en":"Elapsed","sv":"Förfluten","de":"Vergangen","fr":"Écoulé","es":"Transcurrido","zh":"已用时","ja":"経過","ko":"경과"},
"eta":          {"fi":"Jäljellä","en":"Remaining","sv":"Återstår","de":"Verbleibend","fr":"Restant","es":"Restante","zh":"剩余","ja":"残り","ko":"남은"},
"log_lbl":      {"fi":"LOGI","en":"LOG","sv":"LOGG","de":"PROTOKOLL","fr":"JOURNAL","es":"REGISTRO","zh":"日志","ja":"ログ","ko":"로그"},
"fetching":     {"fi":"Haetaan tietoja...","en":"Fetching info...","sv":"Hämtar...","de":"Abrufen...","fr":"Récupération...","es":"Obteniendo...","zh":"获取中...","ja":"取得中...","ko":"가져오는 중..."},
"found_n":      {"fi":"Löydetty {n} videota","en":"Found {n} video(s)","sv":"Hittade {n}","de":"{n} gefunden","fr":"{n} trouvée(s)","es":"{n} encontrado(s)","zh":"找到 {n} 个","ja":"{n}件","ko":"{n}개 발견"},
"log_ok":       {"fi":"OK","en":"OK","sv":"OK","de":"OK","fr":"OK","es":"OK","zh":"OK","ja":"OK","ko":"OK"},
"log_fail":     {"fi":"EPÄONNISTUI","en":"FAILED","sv":"MISSLYCKADES","de":"FEHLGESCHLAGEN","fr":"ÉCHOUÉ","es":"FALLIDO","zh":"失败","ja":"失敗","ko":"실패"},
"summary":      {"fi":"Ladattu: {ok}  |  Virheitä: {err}","en":"Downloaded: {ok}  |  Errors: {err}","sv":"Ned: {ok}  |  Fel: {err}","de":"DL: {ok}  |  Fehler: {err}","fr":"DL: {ok}  |  Err: {err}","es":"DL: {ok}  |  Err: {err}","zh":"{ok}下载 {err}错误","ja":"DL:{ok} 失敗:{err}","ko":"DL:{ok} 오류:{err}"},
"tab_conv":     {"fi":"  MP3 → OGG  ","en":"  MP3 → OGG  ","sv":"  MP3 → OGG  ","de":"  MP3 → OGG  ","fr":"  MP3 → OGG  ","es":"  MP3 → OGG  ","zh":"  MP3 → OGG  ","ja":"  MP3 → OGG  ","ko":"  MP3 → OGG  "},
"tab_yt":       {"fi":"  YouTube  ","en":"  YouTube  ","sv":"  YouTube  ","de":"  YouTube  ","fr":"  YouTube  ","es":"  YouTube  ","zh":"  YouTube  ","ja":"  YouTube  ","ko":"  YouTube  "},
"auto_found":   {"fi":"✓ Löydetty: My Winter Car","en":"✓ Auto-detected: My Winter Car","sv":"✓ Hittades: My Winter Car","de":"✓ Gefunden: My Winter Car","fr":"✓ Détecté: My Winter Car","es":"✓ Detectado: My Winter Car","zh":"✓ 检测到: My Winter Car","ja":"✓ 検出: My Winter Car","ko":"✓ 감지됨: My Winter Car"},
"auto_miss":    {"fi":"Ei löydetty — valitse manuaalisesti","en":"Not found — select manually","sv":"Hittades inte","de":"Nicht gefunden","fr":"Non détecté","es":"No detectado","zh":"未检测到","ja":"未検出","ko":"미감지"},
"auto_saved":   {"fi":"✓ Muistettu","en":"✓ Remembered","sv":"✓ Sparad","de":"✓ Gespeichert","fr":"✓ Mémorisé","es":"✓ Guardado","zh":"✓ 已记住","ja":"✓ 記憶済み","ko":"✓ 저장됨"},
"accent_label": {"fi":"Väri","en":"Color","sv":"Färg","de":"Farbe","fr":"Couleur","es":"Color","zh":"颜色","ja":"カラー","ko":"색상"},
"dark_th":      {"fi":"Tumma","en":"Dark","sv":"Mörkt","de":"Dunkel","fr":"Sombre","es":"Oscuro","zh":"深色","ja":"ダーク","ko":"다크"},
"notif_conv_title": {"fi":"Konvertointi valmis","en":"Conversion complete","sv":"Konvertering klar","de":"Konvertierung fertig","fr":"Conversion terminée","es":"Conversión completa","zh":"转换完成","ja":"変換完了","ko":"변환 완료"},
"notif_conv_msg":   {"fi":"{ok} tiedostoa konvertoitu","en":"{ok} file(s) converted","sv":"{ok} fil(er) konverterade","de":"{ok} Datei(en) konvertiert","fr":"{ok} fichier(s) converti(s)","es":"{ok} archivo(s) convertido(s)","zh":"{ok} 个文件已转换","ja":"{ok}件変換完了","ko":"{ok}개 파일 변환 완료"},
"notif_conv_err":   {"fi":"{ok} ok, {err} epäonnistui","en":"{ok} ok, {err} failed","sv":"{ok} ok, {err} misslyckades","de":"{ok} ok, {err} fehlgeschlagen","fr":"{ok} ok, {err} échoués","es":"{ok} ok, {err} fallidos","zh":"{ok}成功 {err}失败","ja":"{ok}成功 {err}失敗","ko":"{ok}성공 {err}실패"},
"notif_dl_title":   {"fi":"Lataus valmis","en":"Download complete","sv":"Nedladdning klar","de":"Download fertig","fr":"Téléchargement terminé","es":"Descarga completa","zh":"下载完成","ja":"ダウンロード完了","ko":"다운로드 완료"},
"notif_dl_msg":     {"fi":"{ok} video ladattu","en":"{ok} video(s) downloaded","sv":"{ok} video(r) nedladdade","de":"{ok} Video(s) heruntergeladen","fr":"{ok} vidéo(s) téléchargée(s)","es":"{ok} vídeo(s) descargado(s)","zh":"{ok} 个视频已下载","ja":"{ok}件ダウンロード完了","ko":"{ok}개 동영상 다운로드 완료"},
"notif_dl_err":     {"fi":"{ok} ok, {err} epäonnistui","en":"{ok} ok, {err} failed","sv":"{ok} ok, {err} misslyckades","de":"{ok} ok, {err} fehlgeschlagen","fr":"{ok} ok, {err} échoués","es":"{ok} ok, {err} fallidos","zh":"{ok}成功 {err}失败","ja":"{ok}成功 {err}失敗","ko":"{ok}성공 {err}실패"},
"src_folder":   {"fi":"LÄHDE  (MP3-tiedostot)","en":"SOURCE  (MP3 files)","sv":"KÄLLA  (MP3-filer)","de":"QUELLE  (MP3-Dateien)","fr":"SOURCE  (fichiers MP3)","es":"ORIGEN  (archivos MP3)","zh":"源文件夹  (MP3文件)","ja":"ソース  (MP3ファイル)","ko":"소스  (MP3 파일)"},
"dst_folder":   {"fi":"KOHDE  (My Winter Car Radio)","en":"DESTINATION  (My Winter Car Radio)","sv":"MÅL  (My Winter Car Radio)","de":"ZIEL  (My Winter Car Radio)","fr":"DESTINATION  (My Winter Car Radio)","es":"DESTINO  (My Winter Car Radio)","zh":"目标  (My Winter Car Radio)","ja":"保存先  (My Winter Car Radio)","ko":"대상  (My Winter Car Radio)"},
"drop_mp3":     {"fi":"Pudota MP3-tiedostoja tähän","en":"Drop MP3 files here","sv":"Släpp MP3-filer här","de":"MP3-Dateien hier ablegen","fr":"Déposez des MP3 ici","es":"Suelta MP3 aquí","zh":"将MP3文件拖放到此处","ja":"MP3ファイルをここにドロップ","ko":"MP3 파일을 여기에 드롭"},
"sel_all":      {"fi":"Kaikki","en":"Select All","sv":"Välj alla","de":"Alle","fr":"Tout","es":"Todo","zh":"全选","ja":"全選択","ko":"전체"},
"sel_none":     {"fi":"Poista valinnat","en":"Deselect All","sv":"Avmarkera alla","de":"Alle abwählen","fr":"Tout désélectionner","es":"Deseleccionar todo","zh":"取消全选","ja":"全選択解除","ko":"전체 해제"},
"sel_n":        {"fi":"{n} valittu","en":"{n} selected","sv":"{n} valda","de":"{n} gewählt","fr":"{n} sélectionné","es":"{n} selec.","zh":"已选{n}","ja":"{n}件選択","ko":"{n}개 선택"},
"drop_hint":    {"fi":"Pudota MP3-tiedostoja tähän","en":"Drop MP3 files here","sv":"Släpp MP3-filer här","de":"MP3-Dateien hier ablegen","fr":"Déposez des MP3 ici","es":"Suelta MP3 aquí","zh":"将MP3文件拖到此处","ja":"MP3ファイルをここにドロップ","ko":"MP3 파일을 여기에 드롭"},
"preview_title":{"fi":"ESIKATSELU","en":"PREVIEW","sv":"FÖRHANDSGRANSKNING","de":"VORSCHAU","fr":"APERÇU","es":"VISTA PREVIA","zh":"预览","ja":"プレビュー","ko":"미리보기"},
"preview_btn":  {"fi":"Hae tiedot","en":"Fetch Info","sv":"Hämta info","de":"Info holen","fr":"Récupérer infos","es":"Obtener info","zh":"获取信息","ja":"情報取得","ko":"정보 가져오기"},
"preview_none": {"fi":"Liitä URL ja paina Hae tiedot","en":"Paste URL and press Fetch Info","sv":"Klistra in URL och tryck Hämta","de":"URL einfügen und Info holen","fr":"Coller URL et récupérer","es":"Pegar URL y obtener info","zh":"粘贴链接并点击获取","ja":"URLを貼り付けて情報を取得","ko":"URL을 붙여넣고 정보 가져오기"},
"queue_label":  {"fi":"JONO","en":"QUEUE","sv":"KÖ","de":"WARTESCHLANGE","fr":"FILE D'ATTENTE","es":"COLA","zh":"队列","ja":"キュー","ko":"대기열"},
"queue_add":    {"fi":"+ Lisää jonoon","en":"+ Add to Queue","sv":"+ Lägg i kö","de":"+ Zur Warteschlange","fr":"+ Ajouter à la file","es":"+ Añadir a cola","zh":"+ 添加到队列","ja":"+ キューに追加","ko":"+ 대기열에 추가"},
"queue_clear":  {"fi":"Tyhjennä","en":"Clear","sv":"Rensa","de":"Leeren","fr":"Effacer","es":"Limpiar","zh":"清空","ja":"クリア","ko":"지우기"},
"queue_empty":  {"fi":"Jono on tyhjä","en":"Queue is empty","sv":"Kön är tom","de":"Warteschlange leer","fr":"File vide","es":"Cola vacía","zh":"队列为空","ja":"キューが空です","ko":"대기열이 비어있음"},
"history_tab":  {"fi":"  Historia  ","en":"  History  ","sv":"  Historik  ","de":"  Verlauf  ","fr":"  Historique  ","es":"  Historial  ","zh":"  历史  ","ja":"  履歴  ","ko":"  기록  "},
"history_empty":{"fi":"Ei historiatietoja","en":"No history yet","sv":"Ingen historik","de":"Kein Verlauf","fr":"Pas d'historique","es":"Sin historial","zh":"暂无历史记录","ja":"履歴がありません","ko":"기록 없음"},
"history_clear":{"fi":"Tyhjennä historia","en":"Clear History","sv":"Rensa historik","de":"Verlauf löschen","fr":"Effacer l'historique","es":"Borrar historial","zh":"清除历史","ja":"履歴を消去","ko":"기록 지우기"},
"hist_conv":    {"fi":"Konvertointi","en":"Conversion","sv":"Konvertering","de":"Konvertierung","fr":"Conversion","es":"Conversión","zh":"转换","ja":"変換","ko":"변환"},
"hist_dl":      {"fi":"Lataus","en":"Download","sv":"Nedladdning","de":"Download","fr":"Téléchargement","es":"Descarga","zh":"下载","ja":"ダウンロード","ko":"다운로드"},
"update_avail": {"fi":"Päivitys saatavilla: v{ver}","en":"Update available: v{ver}","sv":"Uppdatering tillgänglig: v{ver}","de":"Update verfügbar: v{ver}","fr":"Mise à jour disponible: v{ver}","es":"Actualización disponible: v{ver}","zh":"有新版本: v{ver}","ja":"アップデート: v{ver}","ko":"업데이트: v{ver}"},
"update_btn":   {"fi":"Lataa päivitys","en":"Download Update","sv":"Ladda ner uppdatering","de":"Update herunterladen","fr":"Télécharger la mise à jour","es":"Descargar actualización","zh":"下载更新","ja":"更新をダウンロード","ko":"업데이트 다운로드"},
"update_none":  {"fi":"Käytät uusinta versiota","en":"You have the latest version","sv":"Du har senaste versionen","de":"Neueste Version vorhanden","fr":"Version la plus récente","es":"Tienes la última versión","zh":"您已是最新版本","ja":"最新バージョンです","ko":"최신 버전입니다"},
"tray_open":    {"fi":"Avaa","en":"Open","sv":"Öppna","de":"Öffnen","fr":"Ouvrir","es":"Abrir","zh":"打开","ja":"開く","ko":"열기"},
"tray_quit":    {"fi":"Sulje","en":"Quit","sv":"Avsluta","de":"Beenden","fr":"Quitter","es":"Salir","zh":"退出","ja":"終了","ko":"종료"},
"tut_skip":     {"fi":"Ohita","en":"Skip","sv":"Hoppa över","de":"Überspringen","fr":"Passer","es":"Omitir","zh":"跳过","ja":"スキップ","ko":"건너뛰기"},
"tut_next":     {"fi":"Seuraava →","en":"Next →","sv":"Nästa →","de":"Weiter →","fr":"Suivant →","es":"Siguiente →","zh":"下一步 →","ja":"次へ →","ko":"다음 →"},
"tut_finish":   {"fi":"Aloita käyttö!","en":"Get started!","sv":"Kom igång!","de":"Loslegen!","fr":"Commencer!","es":"¡Empezar!","zh":"开始使用！","ja":"始めよう！","ko":"시작하기!"},
"tut_more":     {"fi":"Haluatko oppia lisää?","en":"Want to learn more?","sv":"Vill du lära dig mer?","de":"Mehr erfahren?","fr":"En savoir plus?","es":"¿Quieres saber más?","zh":"想了解更多？","ja":"もっと詳しく？","ko":"더 알아볼까요?"},
"tut_yes":      {"fi":"Kyllä, näytä lisää","en":"Yes, show me more","sv":"Ja, visa mer","de":"Ja, zeig mir mehr","fr":"Oui, montrez-moi","es":"Sí, muéstrame más","zh":"是的，继续","ja":"はい、もっと見る","ko":"네, 더 보기"},
"tut_no":       {"fi":"Ei kiitos","en":"No thanks","sv":"Nej tack","de":"Nein danke","fr":"Non merci","es":"No gracias","zh":"不用了","ja":"いいえ","ko":"괜찮아요"},
"tut1_title":   {"fi":"Teema & kieli","en":"Theme & Language","sv":"Tema & Språk","de":"Design & Sprache","fr":"Thème & Langue","es":"Tema e Idioma","zh":"主题与语言","ja":"テーマと言語","ko":"테마 & 언어"},
"tut1_body":    {"fi":"Vaihda tumma/vaalea teema tai käyttöliittymän kieli täältä. Voit myös vaihtaa aksenttivärin.","en":"Switch between dark and light theme, change the language, or pick an accent color — all from the top-right corner.","sv":"Växla tema, språk eller accentfärg härifrån.","de":"Design, Sprache und Akzentfarbe oben rechts ändern.","fr":"Changez le thème, la langue ou la couleur d'accentuation ici.","es":"Cambia tema, idioma o color de acento aquí.","zh":"在右上角切换主题、语言或强调色。","ja":"右上からテーマ、言語、アクセントカラーを変更できます。","ko":"오른쪽 상단에서 테마, 언어, 강조색을 변경하세요."},
"tut2_title":   {"fi":"Välilehdet","en":"Tabs","sv":"Flikar","de":"Tabs","fr":"Onglets","es":"Pestañas","zh":"标签页","ja":"タブ","ko":"탭"},
"tut2_body":    {"fi":"Kolme välilehteä: MP3→OGG konvertoi tiedostoja, YouTube lataa musiikkia suoraan, Historia näyttää aiemmat toiminnot.","en":"Three tabs: MP3→OGG converts your files, YouTube downloads music directly, History shows past activity.","sv":"Tre flikar: konvertera, ladda ned från YouTube, historik.","de":"Drei Tabs: Konvertieren, YouTube-Download, Verlauf.","fr":"Trois onglets: convertir, télécharger YouTube, historique.","es":"Tres pestañas: convertir, descargar YouTube, historial.","zh":"三个标签：MP3转换、YouTube下载、历史记录。","ja":"3つのタブ：変換、YouTubeダウンロード、履歴。","ko":"3개 탭: MP3변환, 유튜브 다운로드, 기록."},
"tut3_title":   {"fi":"Lähde ja kohde","en":"Source & Destination","sv":"Källa & Mål","de":"Quelle & Ziel","fr":"Source & Destination","es":"Origen y Destino","zh":"源文件夹与目标","ja":"ソースと保存先","ko":"소스 & 대상"},
"tut3_body":    {"fi":"Lähde on kansio jossa MP3-tiedostosi ovat. Kohde on My Winter Car Radio -kansio — MTO löytää sen automaattisesti Steamista.","en":"Source is the folder with your MP3 files. Destination is your My Winter Car Radio folder — MTO finds it automatically via Steam.","sv":"Källa är mappen med MP3-filer. Mål är My Winter Car Radio-mappen.","de":"Quelle enthält MP3-Dateien. Ziel ist der My Winter Car Radio-Ordner.","fr":"Source: vos MP3. Destination: dossier Radio de My Winter Car.","es":"Origen: tus MP3. Destino: carpeta Radio de My Winter Car.","zh":"源是MP3文件夹，目标是My Winter Car Radio文件夹。","ja":"ソースはMP3フォルダ、保存先はMy Winter Car Radioフォルダ。","ko":"소스는 MP3 폴더, 대상은 My Winter Car Radio 폴더입니다."},
"tut4_title":   {"fi":"Konvertointi","en":"Conversion","sv":"Konvertering","de":"Konvertierung","fr":"Conversion","es":"Conversión","zh":"转换","ja":"変換","ko":"변환"},
"tut4_body":    {"fi":"Valitse tiedostot checkboxeilla, järjestä ↑↓ napeilla ja paina Käynnistä konvertointi. Trackit nimetään automaattisesti.","en":"Select files with checkboxes, reorder with ↑↓, then press Start Conversion. Tracks are named automatically.","sv":"Välj filer, sortera och starta konverteringen.","de":"Dateien auswählen, sortieren und Konvertierung starten.","fr":"Sélectionner, trier et lancer la conversion.","es":"Selecciona, ordena y convierte.","zh":"勾选文件，调整顺序，点击开始转换。","ja":"ファイルを選択、並び替え、変換開始。","ko":"파일 선택, 순서 조정, 변환 시작."},
"tut5_title":   {"fi":"YouTube-lataus","en":"YouTube Download","sv":"YouTube-nedladdning","de":"YouTube-Download","fr":"Téléchargement YouTube","es":"Descarga YouTube","zh":"YouTube下载","ja":"YouTubeダウンロード","ko":"유튜브 다운로드"},
"tut5_body":    {"fi":"Liitä YouTube-linkki, paina Hae tiedot esikatselua varten, lisää jonoon ja lataa. Tiedostot tallentuvat suoraan My Winter Car Radioon.","en":"Paste a YouTube link, press Fetch Info for a preview, add to queue and download. Files save directly to My Winter Car Radio.","sv":"Klistra in länk, förhandsgranska och ladda ned.","de":"Link einfügen, Vorschau abrufen und herunterladen.","fr":"Coller le lien, prévisualiser et télécharger.","es":"Pegar enlace, previsualizar y descargar.","zh":"粘贴链接，预览，下载到游戏。","ja":"リンクを貼り付け、プレビューしてダウンロード。","ko":"링크 붙여넣기, 미리보기, 다운로드."},
"conv_speed":   {"fi":"KONVERTOINTINOPEUS","en":"CONVERSION SPEED","sv":"KONVERTERINGSHASTIGHET","de":"KONVERTIERUNGSGESCHWINDIGKEIT","fr":"VITESSE DE CONVERSION","es":"VELOCIDAD DE CONVERSIÓN","zh":"转换速度","ja":"変換速度","ko":"변환 속도"},
"speed_low":    {"fi":"Matala","en":"Low","sv":"Låg","de":"Niedrig","fr":"Faible","es":"Baja","zh":"低","ja":"低","ko":"낮음"},
"speed_med":    {"fi":"Normaali","en":"Normal","sv":"Normal","de":"Normal","fr":"Normal","es":"Normal","zh":"正常","ja":"普通","ko":"보통"},
"speed_high":   {"fi":"Korkea","en":"High","sv":"Hög","de":"Hoch","fr":"Élevé","es":"Alta","zh":"高","ja":"高","ko":"높음"},
"speed_hint":   {"fi":"Korkea käyttää enemmän CPU:ta","en":"High uses more CPU","sv":"Hög använder mer CPU","de":"Hoch nutzt mehr CPU","fr":"Élevé utilise plus de CPU","es":"Alta usa más CPU","zh":"高使用更多CPU","ja":"高はCPUを多く使用","ko":"높음은 CPU를 더 사용"},
"whats_new":    {"fi":"Mitä uutta","en":"What's New","sv":"Vad är nytt","de":"Was ist neu","fr":"Nouveautés","es":"Novedades","zh":"更新内容","ja":"新機能","ko":"새로운 기능"},
"update_later": {"fi":"Myöhemmin","en":"Later","sv":"Senare","de":"Später","fr":"Plus tard","es":"Más tarde","zh":"稍后","ja":"後で","ko":"나중에"},
"settings_tab":  {"fi":"  Asetukset  ","en":"  Settings  ","sv":"  Inställningar  ","de":"  Einstellungen  ","fr":"  Paramètres  ","es":"  Ajustes  ","zh":"  设置  ","ja":"  設定  ","ko":"  설정  "},
"settings_app":  {"fi":"SOVELLUS","en":"APPLICATION","sv":"PROGRAM","de":"ANWENDUNG","fr":"APPLICATION","es":"APLICACIÓN","zh":"应用","ja":"アプリ","ko":"앱"},
"settings_appear":{"fi":"ULKOASU","en":"APPEARANCE","sv":"UTSEENDE","de":"ERSCHEINUNGSBILD","fr":"APPARENCE","es":"APARIENCIA","zh":"外观","ja":"外観","ko":"외관"},
"settings_lang": {"fi":"Kieli","en":"Language","sv":"Språk","de":"Sprache","fr":"Langue","es":"Idioma","zh":"语言","ja":"言語","ko":"언어"},
"settings_theme":{"fi":"Teema","en":"Theme","sv":"Tema","de":"Design","fr":"Thème","es":"Tema","zh":"主题","ja":"テーマ","ko":"테마"},
"settings_accent":{"fi":"Aksenttiväri","en":"Accent Color","sv":"Accentfärg","de":"Akzentfarbe","fr":"Couleur d'accent","es":"Color de acento","zh":"强调色","ja":"アクセントカラー","ko":"강조 색상"},
"settings_font": {"fi":"Fonttikoko","en":"Font Size","sv":"Teckenstorlek","de":"Schriftgröße","fr":"Taille de police","es":"Tamaño de fuente","zh":"字体大小","ja":"フォントサイズ","ko":"글꼴 크기"},
"font_small":    {"fi":"Pieni","en":"Small","sv":"Liten","de":"Klein","fr":"Petit","es":"Pequeño","zh":"小","ja":"小","ko":"작음"},
"font_normal":   {"fi":"Normaali","en":"Normal","sv":"Normal","de":"Normal","fr":"Normal","es":"Normal","zh":"正常","ja":"普通","ko":"보통"},
"font_large":    {"fi":"Suuri","en":"Large","sv":"Stor","de":"Groß","fr":"Grand","es":"Grande","zh":"大","ja":"大","ko":"큼"},
"settings_tools":{"fi":"TYÖKALUT","en":"TOOLS","sv":"VERKTYG","de":"WERKZEUGE","fr":"OUTILS","es":"HERRAMIENTAS","zh":"工具","ja":"ツール","ko":"도구"},
"uninstall_tools":{"fi":"Poista FFmpeg & yt-dlp","en":"Uninstall FFmpeg & yt-dlp","sv":"Avinstallera FFmpeg & yt-dlp","de":"FFmpeg & yt-dlp deinstallieren","fr":"Désinstaller FFmpeg & yt-dlp","es":"Desinstalar FFmpeg & yt-dlp","zh":"卸载 FFmpeg & yt-dlp","ja":"FFmpeg & yt-dlpをアンインストール","ko":"FFmpeg & yt-dlp 제거"},
"reset_settings":{"fi":"Nollaa asetukset","en":"Reset Settings","sv":"Återställ inställningar","de":"Einstellungen zurücksetzen","fr":"Réinitialiser les paramètres","es":"Restablecer ajustes","zh":"重置设置","ja":"設定をリセット","ko":"설정 초기화"},
"check_updates": {"fi":"Tarkista päivitykset","en":"Check for Updates","sv":"Sök efter uppdateringar","de":"Nach Updates suchen","fr":"Rechercher des mises à jour","es":"Buscar actualizaciones","zh":"检查更新","ja":"アップデートを確認","ko":"업데이트 확인"},
"up_to_date":    {"fi":"Käytät uusinta versiota","en":"You're up to date","sv":"Du har senaste versionen","de":"Sie haben die neueste Version","fr":"Vous êtes à jour","es":"Estás actualizado","zh":"已是最新版本","ja":"最新バージョンです","ko":"최신 버전입니다"},
"uninstall_done":{"fi":"Poistettu. Käynnistä uudelleen asentaaksesi.","en":"Removed. Restart to reinstall.","sv":"Borttaget. Starta om för att installera om.","de":"Entfernt. Neu starten zum Neuinstallieren.","fr":"Supprimé. Redémarrez pour réinstaller.","es":"Eliminado. Reinicia para reinstalar.","zh":"已删除。重启以重新安装。","ja":"削除しました。再起動して再インストール。","ko":"제거됨. 재설치하려면 재시작하세요."},
"light_th":     {"fi":"Vaalea","en":"Light","sv":"Ljust","de":"Hell","fr":"Clair","es":"Claro","zh":"浅色","ja":"ライト","ko":"라이트"},
}

LANG_OPTIONS = [
    ("en","🇬🇧  English"),("fi","🇫🇮  Suomi"),("sv","🇸🇪  Svenska"),
    ("de","🇩🇪  Deutsch"),("fr","🇫🇷  Français"),("es","🇪🇸  Español"),
    ("zh","🇨🇳  中文"),("ja","🇯🇵  日本語"),("ko","🇰🇷  한국어"),
]

ACCENT_PRESETS = [
    ("#7b68ee","Violet"),("#c8ff00","Acid"),("#00d4aa","Teal"),
    ("#ff6b6b","Coral"),("#ffd93d","Gold"),("#6bcb77","Mint"),
    ("#4d96ff","Blue"),("#ff922b","Orange"),
]

def t(key, **kw):
    s = STRINGS.get(key,{}).get(_lang) or STRINGS.get(key,{}).get("en",key)
    for k,v in kw.items(): s = s.replace("{"+k+"}",str(v))
    return s

def deps_ok(): return os.path.isfile(FFMPEG) and os.path.isfile(YTDLP)

HISTORY_FILE = os.path.join(APP_DIR, "history.json")

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_history_entry(entry: dict):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        h = load_history()
        h.insert(0, entry)
        h = h[:200]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(h, f, indent=2, ensure_ascii=False)
    except: pass

def clear_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump([], f)
    except: pass

def check_for_update():
    """Returns (latest_version_str, download_url, changelog) or (None, None, None)."""
    log.info(f"Checking for updates (current: {APP_VERSION})")
    try:
        req = urllib.request.Request(GITHUB_API,
            headers={"User-Agent": "MTO-Updater"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        tag = data.get("tag_name", "")
        if tag.startswith("v") or tag.startswith("V"):
            tag = tag[1:]
        assets = data.get("assets", [])
        url = next((a["browser_download_url"] for a in assets
                    if a["name"].lower().endswith(".zip")), None)
        if not url:
            url = next((a["browser_download_url"] for a in assets
                        if a["name"].lower().endswith(".exe")), None)
        changelog = data.get("body", "").strip()
        def _parse_ver(v):
            try:
                parts = v.split("-", 1)
                base = tuple(int(x) for x in parts[0].split("."))
                suffix = 1 if len(parts) == 1 else 0  
                return base + (suffix,)
            except: return (0,)
        if tag and url and _parse_ver(tag) > _parse_ver(APP_VERSION):
            log.info(f"Update available: {tag}")
            return tag, url, changelog
        else:
            log.info(f"No update found (latest: {tag})")
    except Exception as e:
        log.error(f"Update check failed: {e}")
    return None, None, None

def download_update(url: str, progress_cb=None):
    """
    Download update ZIP, extract MTO.exe as MTO_new.exe,
    delete ZIP, write update.bat, return bat path.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        zip_path = os.path.join(base_dir, "MTO_update.zip")
        new_exe  = os.path.join(base_dir, "MTO_new.exe")
        bat_path = os.path.join(base_dir, "update.bat")

        download_with_progress(url, zip_path, pcb=progress_cb)

        import zipfile as _zf
        with _zf.ZipFile(zip_path, "r") as z:
            exe_names = [n for n in z.namelist() if n.lower().endswith(".exe")]
            if not exe_names:
                os.remove(zip_path)
                return None
            with z.open(exe_names[0]) as src, open(new_exe, "wb") as dst:
                shutil.copyfileobj(src, dst)

        os.remove(zip_path)

        bat = (
            "@echo off\n"
            ":loop\n"
            "move /y \"MTO_new.exe\" \"MTO.exe\" >nul 2>&1\n"
            "if errorlevel 1 (\n"
            "    timeout /t 1 /nobreak >nul\n"
            "    goto loop\n"
            ")\n"
            "start \"\" \"MTO.exe\"\n"
            "del \"%~f0\"\n"
        )
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat)

        return bat_path
    except Exception as e:
        for p in [zip_path, new_exe]:
            try:
                if os.path.exists(p): os.remove(p)
            except: pass
        return None

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

def make_tray_icon():
    """Create a simple programmatic tray icon."""
    if not HAS_TRAY: return None
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 2, 62, 62], radius=14, fill="#7b68ee")
    d.polygon([(18,32),(42,20),(42,27),(54,27),(54,37),(42,37),(42,44)], fill="white")
    return img

_config_lock = threading.Lock()

def load_config():
    try:
        with open(CONFIG_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_config(data):
    with _config_lock:
        try:
            os.makedirs(APP_DIR,exist_ok=True)
            ex=load_config(); ex.update(data)
            with open(CONFIG_FILE,"w",encoding="utf-8") as f:
                json.dump(ex,f,indent=2,ensure_ascii=False)
        except: pass

def find_mwc_radio():
    log.debug('Searching for My Winter Car via Steam registry')
    try:
        import winreg
        k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Valve\Steam")
        sp,_=winreg.QueryValueEx(k,"SteamPath"); winreg.CloseKey(k)
        sp=sp.replace("/","\\")
    except: return None,None
    vdf=os.path.join(sp,"steamapps","libraryfolders.vdf"); libs=[sp]
    if os.path.isfile(vdf):
        try:
            with open(vdf,"r",encoding="utf-8") as f: d=f.read()
            for p in re.findall(r'"path"\s+"([^"]+)"',d): libs.append(p.replace("\\\\","\\"))
        except: pass
    sub=os.path.join("steamapps","common","My Winter Car","Radio")
    for lib in libs:
        c=os.path.join(lib,sub)
        if os.path.isdir(c): return c,lib
    return None,None

def download_with_progress(url,dest,pcb=None,scb=None):
    os.makedirs(os.path.dirname(dest),exist_ok=True)
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        total=int(r.headers.get("Content-Length",0)); done=0
        with open(dest,"wb") as f:
            while True:
                chunk=r.read(65536)
                if not chunk: break
                f.write(chunk); done+=len(chunk)
                if pcb and total: pcb(done/total)
                if scb and total: scb(f"{done/1e6:.1f} MB / {total/1e6:.1f} MB")

def install_ffmpeg(pcb=None,scb=None,lcb=None):
    zp=os.path.join(BIN_DIR,"ffmpeg_temp.zip")
    log.info("Downloading FFmpeg...")
    if lcb: lcb("Ladataan FFmpeg...  (~70 MB)")
    download_with_progress(FFMPEG_URL,zp,pcb,scb)
    log.info("Extracting FFmpeg...")
    if lcb: lcb("Puretaan FFmpeg...")
    with zipfile.ZipFile(zp) as z:
        for m in z.namelist():
            if m.endswith("bin/ffmpeg.exe"):
                with z.open(m) as s, open(FFMPEG,"wb") as d: shutil.copyfileobj(s,d)
                break
    os.remove(zp)

def install_ytdlp(pcb=None,scb=None,lcb=None):
    log.info("Downloading yt-dlp...")
    if lcb: lcb("Ladataan yt-dlp...  (~10 MB)")
    os.makedirs(BIN_DIR,exist_ok=True)
    download_with_progress(YTDLP_URL,YTDLP,pcb,scb)

def get_mp3s(folder):
    try: return sorted(f for f in os.listdir(folder) if f.lower().endswith(".mp3"))
    except PermissionError: return []
    except Exception: return []
def get_tracks(folder):
    nums=set()
    for f in os.listdir(folder):
        if f.lower().startswith("track") and f.lower().endswith(".ogg"):
            try: nums.add(int(f[5:-4]))
            except: pass
    return nums
def next_free(ex,start=1,limit=200):
    for i in range(start,limit+1):
        if i not in ex: return i
    return None
def run_h(*a,**k): return subprocess.run(*a,creationflags=NO_WINDOW,**k)
def fmt_t(s):
    if s is None or s<0: return "--:--"
    s=int(s); m,s=divmod(s,60); h,m=divmod(m,60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def card(master,**kw):
    kw.setdefault("fg_color",TH("surface")); kw.setdefault("corner_radius",12)
    kw.setdefault("border_width",1); kw.setdefault("border_color",TH("border"))
    return ctk.CTkFrame(master,**kw)

class FileRow(ctk.CTkFrame):
    """A single row in the file list showing filename, target track, status dot,
    checkbox and up/down reorder buttons.
    """

    def __init__(self, master, filename, track, on_move_up, on_move_down, on_check_change=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._on_check_change = on_check_change
        self.columnconfigure(1, weight=1)

        self.cb_var = ctk.BooleanVar(value=True)
        self.cb = ctk.CTkCheckBox(self, text="", variable=self.cb_var, width=24,
            checkbox_width=18, checkbox_height=18,
            fg_color=TH("accent"), hover_color=TH("acc_hi"),
            border_color=TH("border"), checkmark_color=TH("bg"),
            command=self._on_check)
        self.cb.grid(row=0, column=0, padx=(0, 4))

        self.dot = ctk.CTkLabel(self, text="○", font=("Segoe UI", 13),
                                text_color=TH("subtext"), width=22)
        self.dot.grid(row=0, column=1, padx=(0, 4))

        self.name_lbl = ctk.CTkLabel(self, text=filename, font=("Segoe UI", 12),
                                     text_color=TH("text"), anchor="w")
        self.name_lbl.grid(row=0, column=2, sticky="ew", padx=4)

        ctk.CTkLabel(self, text="→", font=("Segoe UI", 12),
                     text_color=TH("muted")).grid(row=0, column=3, padx=4)

        self.tl = ctk.CTkLabel(self, text=track, font=("Consolas", 11, "bold"),
                               text_color=TH("accent"), width=110, anchor="w")
        self.tl.grid(row=0, column=4, padx=(0, 6))

        self.btn_up = ctk.CTkButton(self, text="↑", width=26, height=26,
            font=("Segoe UI", 11), fg_color=TH("surface2"), hover_color=TH("surface3"),
            text_color=TH("subtext"), border_width=1, border_color=TH("border"),
            corner_radius=6, command=on_move_up)
        self.btn_up.grid(row=0, column=5, padx=(0, 2))

        self.btn_dn = ctk.CTkButton(self, text="↓", width=26, height=26,
            font=("Segoe UI", 11), fg_color=TH("surface2"), hover_color=TH("surface3"),
            text_color=TH("subtext"), border_width=1, border_color=TH("border"),
            corner_radius=6, command=on_move_down)
        self.btn_dn.grid(row=0, column=6, padx=(0, 4))

        ctk.CTkFrame(self, height=1, fg_color=TH("border")).grid(
            row=1, column=0, columnspan=7, sticky="ew", pady=(4, 0))

    def _on_check(self):
        checked = self.cb_var.get()
        self.name_lbl.configure(text_color=TH("text") if checked else TH("subtext"))
        self.tl.configure(text_color=TH("accent") if checked else TH("muted"))
        if self._on_check_change:
            self._on_check_change()

    def is_checked(self): return self.cb_var.get()

    def set_status(self, s):
        self._last_status = s
        c, d = {"waiting":(TH("subtext"),"○"),"converting":(TH("warning"),"◉"),
                "done":(TH("success"),"●"),"error":(TH("error"),"✕"),
                "skipped":(TH("muted"),"–")}.get(s, (TH("subtext"), "○"))
        self.dot.configure(text=d, text_color=c)

    def set_track(self, n): self.tl.configure(text=n, text_color=TH("success"))


class TimerBar(ctk.CTkFrame):
    """Displays elapsed time and estimated remaining time during conversion/download."""

    def __init__(self,master,**kw):
        super().__init__(master,fg_color=TH("surface2"),corner_radius=8,
                         border_width=1,border_color=TH("border"),**kw)
        self._s=None; self._tot=0; self._n=0; self._run=False; self._aid=None
        inner=ctk.CTkFrame(self,fg_color="transparent"); inner.pack(side="left",padx=14,pady=6)
        self._el=ctk.CTkLabel(inner,text=t("el"),font=("Segoe UI",11),text_color=TH("subtext"))
        self._el.pack(side="left",padx=(0,5))
        self._ev=ctk.CTkLabel(inner,text="00:00",font=("Consolas",13,"bold"),text_color=TH("text"))
        self._ev.pack(side="left")
        ctk.CTkLabel(inner,text="   ·   ",font=("Segoe UI",11),text_color=TH("border")).pack(side="left")
        self._etal=ctk.CTkLabel(inner,text=t("eta"),font=("Segoe UI",11),text_color=TH("subtext"))
        self._etal.pack(side="left",padx=(0,5))
        self._etav=ctk.CTkLabel(inner,text="--:--",font=("Consolas",13,"bold"),text_color=TH("accent"))
        self._etav.pack(side="left")
    def start(self, total):
        self._s   = time.time()
        self._tot = total
        self._n   = 0
        self._run = True
        self._tick()

    def set_total(self, total):
        self._tot = total

    def update_progress(self, n):
        self._n = n

    def stop(self):
        self._run = False
        if self._aid:
            try: self.after_cancel(self._aid)
            except: pass

    def reset(self):
        self.stop()
        self._n = 0
        try:
            self._ev.configure(text="00:00")
            self._etav.configure(text="--:--")
        except: pass

    def retranslate(self):
        self._el.configure(text=t("el"))
        self._etal.configure(text=t("eta"))

    def _tick(self):
        if not self._run: return
        try:
            el = time.time() - self._s
            self._ev.configure(text=fmt_t(el))
            n   = self._n
            tot = self._tot
            if n > 0 and tot > 0:
                eta = (el / n) * (tot - n)
                self._etav.configure(text=fmt_t(max(0, eta)))
            else:
                self._etav.configure(text="--:--")
        except Exception:
            pass
        self._aid = self.after(300, self._tick)

class SetupFrame(ctk.CTkFrame):
    """First-launch setup wizard that downloads FFmpeg and yt-dlp from GitHub."""

    def __init__(self,master,on_done):
        super().__init__(master,fg_color=TH("bg"))
        self.on_done=on_done; self._widgets={}; self._build()

    def _build(self):
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(side="bottom", fill="x", padx=40, pady=(10,20))
        self._btn = AnimBtn(bot, text=t("btn_install"), variant="accent",
            width=320, height=52, font=("Segoe UI",14,"bold"),
            corner_radius=12, command=self._start)
        self._btn.pack()
        ctk.CTkLabel(bot, text=t("once"), font=("Segoe UI",11),
            text_color=TH("muted")).pack(pady=(6,0))

        pg_bar = ctk.CTkFrame(self, fg_color="transparent")
        pg_bar.pack(side="bottom", fill="x", padx=40, pady=(0,4))
        self._widgets["cur"] = ctk.CTkLabel(pg_bar, text="",
            font=("Segoe UI",11), text_color=TH("text"))
        self._widgets["cur"].pack(anchor="w")
        self._widgets["sz"] = ctk.CTkLabel(pg_bar, text="",
            font=("Consolas",10), text_color=TH("subtext"))
        self._widgets["sz"].pack(anchor="w", pady=(2,6))
        self.bar = ctk.CTkProgressBar(pg_bar, height=6,
            fg_color=TH("border"), progress_color=TH("accent"), corner_radius=3)
        self.bar.pack(fill="x"); self.bar.set(0)

        ctk.CTkLabel(self, text="MTO", font=("Segoe UI",30,"bold"),
            text_color=TH("accent")).pack(pady=(20,2))
        ctk.CTkLabel(self, text=t("setup_title"), font=("Segoe UI",13),
            text_color=TH("subtext")).pack(pady=(0,14))

        ca = card(self); ca.pack(fill="x", padx=30, pady=(0,8))
        ctk.CTkLabel(ca, text="FIRST LAUNCH", font=("Segoe UI",9,"bold"),
            text_color=TH("subtext")).pack(anchor="w",padx=20,pady=(14,6))
        ctk.CTkLabel(ca, text=t("setup_body"), font=("Segoe UI",12),
            text_color=TH("text"), justify="left").pack(anchor="w",padx=20,pady=(0,12))
        ctk.CTkFrame(ca,height=1,fg_color=TH("border")).pack(fill="x")
        pf = ctk.CTkFrame(ca,fg_color=TH("surface2"),corner_radius=0); pf.pack(fill="x")
        ctk.CTkLabel(pf,text=t("install_dir"),font=("Segoe UI",8,"bold"),
            text_color=TH("subtext")).pack(anchor="w",padx=20,pady=(10,3))
        ctk.CTkLabel(pf,text=BIN_DIR,font=("Consolas",10),
            text_color=TH("accent")).pack(anchor="w",padx=20,pady=(0,10))
        ctk.CTkFrame(ca,height=1,fg_color=TH("border")).pack(fill="x")
        deps = ctk.CTkFrame(ca,fg_color="transparent"); deps.pack(fill="x",padx=20,pady=12)
        self.r_ff = self._dep(deps,"FFmpeg",t("ffmpeg_d"),"~70 MB")
        ctk.CTkFrame(deps,height=1,fg_color=TH("border")).pack(fill="x",pady=6)
        self.r_yt = self._dep(deps,"yt-dlp",t("ytdlp_d"),"~10 MB")

    def _dep(self,par,name,desc,size):
        row=ctk.CTkFrame(par,fg_color="transparent"); row.pack(fill="x",pady=2)
        row.columnconfigure(1,weight=1)
        dot=ctk.CTkLabel(row,text="○",font=("Segoe UI",14),text_color=TH("subtext"),width=28)
        dot.grid(row=0,column=0,rowspan=2,sticky="n",pady=2)
        ctk.CTkLabel(row,text=name,font=("Segoe UI",13,"bold"),text_color=TH("text"),anchor="w").grid(row=0,column=1,sticky="w")
        ctk.CTkLabel(row,text=desc,font=("Segoe UI",11),text_color=TH("subtext"),anchor="w").grid(row=1,column=1,sticky="w")
        ctk.CTkLabel(row,text=size,font=("Consolas",10),text_color=TH("muted"),width=60,anchor="e").grid(row=0,column=2,padx=(8,0))
        return {"dot":dot}

    def _sd(self,row,s):
        c,d={"waiting":(TH("subtext"),"○"),"active":(TH("warning"),"◉"),"done":(TH("success"),"●"),"error":(TH("error"),"✕")}.get(s,(TH("subtext"),"○"))
        row["dot"].configure(text=d,text_color=c)

    def _start(self):
        self._btn.configure(state="disabled",text=t("btn_ing"))
        threading.Thread(target=self._install,daemon=True).start()

    def _install(self):
        sl = lambda v: self.after(0, lambda: self._widgets["sz"].configure(text=v))
        ll = lambda v: self.after(0, lambda: self._widgets["cur"].configure(text=v))

        self._anim_running = True
        def animate(dots=0):
            if not self._anim_running: return
            self.after(0, lambda: self._widgets["sz"].configure(
                text="Yhdistetään" + "." * (dots % 4)))
            self.after(400, lambda: animate(dots + 1))
        animate()

        def stop_anim(): self._anim_running = False

        try:
            os.makedirs(BIN_DIR, exist_ok=True)
            if not os.path.isfile(FFMPEG):
                self.after(0, self._sd, self.r_ff, "active")
                self.after(0, ll, "Ladataan FFmpeg...  (~70 MB)")
                install_ffmpeg(
                    lambda p: [stop_anim(), self.after(0, self.bar.set, (p or 0) * 0.75),
                               self.after(0, lambda p=p: sl(f"{(p or 0)*70:.1f} MB / 70 MB"))],
                    None, None)
            self.after(0, self._sd, self.r_ff, "done")
            self.after(0, self.bar.set, 0.75)
            stop_anim()
            if not os.path.isfile(YTDLP):
                self.after(0, self._sd, self.r_yt, "active")
                self.after(0, ll, "Ladataan yt-dlp...  (~10 MB)")
                self._anim_running = True
                animate()
                install_ytdlp(
                    lambda p: [stop_anim(), self.after(0, self.bar.set, 0.75 + (p or 0) * 0.25),
                               self.after(0, lambda p=p: sl(f"{(p or 0)*10:.1f} MB / 10 MB"))],
                    None, None)
            self.after(0, self._sd, self.r_yt, "done")
            self.after(0, self.bar.set, 1.0)
            stop_anim()
            self.after(0, ll, t("done_install"))
            self.after(0, sl, "")
            self.after(900, self.on_done)
        except Exception as e:
            stop_anim()
            self.after(0, ll, f"Virhe: {e}")
            self.after(0, lambda: self._btn.configure(state="normal", text=t("btn_retry")))

class ConverterTab(ctk.CTkFrame):
    """MP3 → OGG conversion tab. Scans a source folder, lets the user select and
    reorder files, then converts them to the My Winter Car Radio destination folder.
    """

    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._src = ""   
        self._dst = ""
        self._mp3s = []; self._rows = []; self._tmap = {}
        self._run = False; self._tw = {}
        self._build()

    def _pill(self, par, key, val):
        f = ctk.CTkFrame(par, fg_color=TH("surface2"), corner_radius=10,
                         border_width=1, border_color=TH("border"))
        f.pack(side="left", padx=(0, 10))
        lbl = ctk.CTkLabel(f, text=t(key), font=("Segoe UI", 11), text_color=TH("subtext"))
        lbl.pack(padx=14, pady=(8, 0))
        v = ctk.CTkLabel(f, text=val, font=("Segoe UI", 20, "bold"), text_color=TH("text"))
        v.pack(padx=14, pady=(0, 8))
        self._tw.setdefault("pills", []).append((lbl, key)); return v

    def _build(self):
        br = ctk.CTkFrame(self, fg_color="transparent")
        br.pack(side="bottom", fill="x", pady=(6, 4))
        self.status = ctk.CTkLabel(br, text=t("ready"), font=("Segoe UI", 12),
                                    text_color=TH("subtext"))
        self.status.pack(side="left")
        self.start_btn = AnimBtn(br, text=t("btn_start"), variant="accent",
            width=260, height=50, font=("Segoe UI", 14, "bold"),
            state="disabled", command=self._start)
        self.start_btn.pack(side="right"); self._tw["start_btn"] = self.start_btn

        self.prog = ctk.CTkProgressBar(self, height=5, fg_color=TH("surface2"),
                                        progress_color=TH("accent"), corner_radius=3)
        self.prog.pack(side="bottom", fill="x", pady=(0, 3)); self.prog.set(0)
        self.timer = TimerBar(self); self.timer.pack(side="bottom", fill="x", pady=(0, 5))

        top = card(self); top.pack(fill="x", pady=(0, 10))
        inner = ctk.CTkFrame(top, fg_color="transparent"); inner.pack(fill="x", padx=18, pady=14)

        sl = ctk.CTkLabel(inner, text=t("src_folder"), font=("Segoe UI", 10, "bold"),
                           text_color=TH("subtext"))
        sl.pack(anchor="w"); self._tw["src_lbl"] = sl
        src_row = ctk.CTkFrame(inner, fg_color="transparent")
        src_row.pack(fill="x", pady=(5, 0))
        self.src_entry = ctk.CTkEntry(src_row, placeholder_text="...", font=("Segoe UI", 13),
            fg_color=TH("surface2"), border_color=TH("border"),
            text_color=TH("text"), height=42, border_width=1)
        self.src_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        bb_src = AnimBtn(src_row, text=t("browse"), width=100, height=42,
                         font=("Segoe UI", 12, "bold"), command=self._browse_src)
        bb_src.pack(side="right"); self._tw["browse_src"] = bb_src

        self._drop_lbl = ctk.CTkLabel(inner, text="", font=("Segoe UI", 9),
                                       text_color=TH("muted"))
        self._drop_lbl.pack(anchor="w", pady=(3, 0))

        ctk.CTkFrame(inner, height=1, fg_color=TH("border")).pack(fill="x", pady=(12, 10))

        dl = ctk.CTkLabel(inner, text=t("dst_folder"), font=("Segoe UI", 10, "bold"),
                           text_color=TH("subtext"))
        dl.pack(anchor="w"); self._tw["dst_lbl"] = dl
        dst_row = ctk.CTkFrame(inner, fg_color="transparent")
        dst_row.pack(fill="x", pady=(5, 0))
        self.dst_entry = ctk.CTkEntry(dst_row, placeholder_text="...", font=("Segoe UI", 13),
            fg_color=TH("surface2"), border_color=TH("border"),
            text_color=TH("text"), height=42, border_width=1)
        self.dst_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        bb_dst = AnimBtn(dst_row, text=t("browse"), width=100, height=42,
                         font=("Segoe UI", 12, "bold"), command=self._browse_dst)
        bb_dst.pack(side="right"); self._tw["browse_dst"] = bb_dst
        self._dst_lbl = ctk.CTkLabel(inner, text="", font=("Segoe UI", 10),
                                      text_color=TH("subtext"))
        self._dst_lbl.pack(anchor="w", pady=(4, 0))

        sr = ctk.CTkFrame(self, fg_color="transparent"); sr.pack(fill="x", pady=(0, 10))
        self.s_mp3  = self._pill(sr, "s_found",  "--")
        self.s_ogg  = self._pill(sr, "s_exists", "--")
        self.s_next = self._pill(sr, "s_next",   "--")
        self.s_free = self._pill(sr, "s_free",   "--")

        sc = card(self); sc.pack(fill="x", pady=(0, 10))
        si = ctk.CTkFrame(sc, fg_color="transparent"); si.pack(fill="x", padx=18, pady=10)
        sl_lbl = ctk.CTkLabel(si, text=t("conv_speed"),
            font=("Segoe UI",10,"bold"), text_color=TH("subtext"))
        sl_lbl.pack(side="left"); self._tw["speed_lbl"] = sl_lbl
        self._speed_val = ctk.CTkLabel(si, text=t("speed_med"),
            font=("Segoe UI",10,"bold"), text_color=TH("accent"), width=60)
        self._speed_val.pack(side="right")
        self._speed_hint = ctk.CTkLabel(si, text="",
            font=("Segoe UI",9), text_color=TH("muted"))
        self._speed_hint.pack(side="right", padx=(0,8))
        self._speed_slider = ctk.CTkSlider(sc, from_=0, to=2, number_of_steps=2,
            fg_color=TH("border"), progress_color=TH("accent"),
            button_color=TH("accent"), button_hover_color=TH("acc_hi"),
            command=self._on_speed_change)
        self._speed_slider.pack(fill="x", padx=18, pady=(0,10))
        cfg_speed = load_config().get("conv_speed", 1)
        self._speed_slider.set(cfg_speed)
        self._on_speed_change(cfg_speed)

        fh = ctk.CTkFrame(self, fg_color="transparent"); fh.pack(fill="x", pady=(0, 5))
        fl = ctk.CTkLabel(fh, text=t("files_lbl"), font=("Segoe UI", 10, "bold"),
                           text_color=TH("subtext"))
        fl.pack(side="left"); self._tw["files_lbl"] = fl
        self.sel_lbl = ctk.CTkLabel(fh, text="", font=("Segoe UI", 10),
                                     text_color=TH("subtext"))
        self.sel_lbl.pack(side="left", padx=(10, 0))
        self._sel_toggle_btn = AnimBtn(fh, text=t("sel_all"), width=110, height=28,
            font=("Segoe UI", 10, "bold"), command=self._toggle_sel)
        self._sel_toggle_btn.pack(side="right")
        self._tw["sel_toggle"] = self._sel_toggle_btn

        lc = card(self); lc.pack(fill="both", expand=True)
        self.scroll = ctk.CTkScrollableFrame(lc, fg_color="transparent",
                                              scrollbar_button_color=TH("border"))
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        el = ctk.CTkLabel(self.scroll, text=t("empty"), font=("Segoe UI", 13),
                           text_color=TH("subtext"))
        el.pack(pady=50); self._tw["empty"] = el

        self._init_folders()

    def _setup_drop(self):
        pass  

    def _init_folders(self):
        cfg = load_config()
        src = cfg.get("src_folder", "")
        if src and os.path.isdir(src):
            self._src = src
            self.src_entry.delete(0, "end"); self.src_entry.insert(0, src)

        dst = cfg.get("folder", "")
        if dst and os.path.isdir(dst):
            self._dst = dst
            self.dst_entry.delete(0, "end"); self.dst_entry.insert(0, dst)
            self._dst_lbl.configure(text=t("auto_saved"), text_color=TH("success"))
        else:
            f, _ = find_mwc_radio()
            if f:
                self._dst = f
                self.dst_entry.delete(0, "end"); self.dst_entry.insert(0, f)
                self._dst_lbl.configure(text=t("auto_found"), text_color=TH("success"))
                save_config({"folder": f})  
            else:
                self._dst_lbl.configure(text=t("auto_miss"), text_color=TH("subtext"))
        if self._src:
            self._scan()

    def _set_src(self, path, silent=False):
        self._src = path
        self.src_entry.delete(0, "end"); self.src_entry.insert(0, path)
        save_config({"src_folder": path})
        self._scan()

    def _set_dst(self, path, msg="", color=None):
        self._dst = path
        self.dst_entry.delete(0, "end"); self.dst_entry.insert(0, path)
        self._dst_lbl.configure(text=msg, text_color=color or TH("success"))
        self._scan()

    def retranslate(self):
        self._tw["src_lbl"].configure(text=t("src_folder"))
        self._tw["dst_lbl"].configure(text=t("dst_folder"))
        for k in ("browse_src", "browse_dst"):
            self._tw[k].configure(text=t("browse"))
        self._tw["files_lbl"].configure(text=t("files_lbl"))

        try: self._tw["empty"].configure(text=t("empty"))
        except: pass
        self.status.configure(text=t("ready"))
        if not self._run: self.start_btn.configure(text=t("btn_start"))
        for lbl, key in self._tw.get("pills", []): lbl.configure(text=t(key))
        self._update_sel_label()
        self.timer.retranslate()

    def _on_speed_change(self, val):
        val = int(round(float(val)))
        labels = [t("speed_low"), t("speed_med"), t("speed_high")]
        hints  = [t("speed_hint"), "", t("speed_hint")]
        self._speed_val.configure(text=labels[val])
        self._speed_hint.configure(text=hints[val])
        save_config({"conv_speed": val})

    def _get_priority(self):
        val = int(round(float(self._speed_slider.get())))
        return {0: 0x00004000, 1: 0x00000020, 2: 0x00008000}.get(val, 0x00000020)

    def _browse_src(self):
        f = filedialog.askdirectory()
        if f: self._set_src(f)

    def _browse_dst(self):
        f = filedialog.askdirectory()
        if f:
            save_config({"folder": f})
            self._set_dst(f, t("auto_saved"))

    def _move(self, idx, direction):
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._mp3s): return
        checks   = {self._mp3s[i]: self._rows[i].is_checked() for i in range(len(self._rows))}
        statuses = {self._mp3s[i]: getattr(self._rows[i], "_last_status", "waiting")
                    for i in range(len(self._rows))}
        self._mp3s[idx], self._mp3s[new_idx] = self._mp3s[new_idx], self._mp3s[idx]
        self._rebuild_rows(checks, statuses)

    def _toggle_sel(self):
        all_checked = all(r.is_checked() for r in self._rows) if self._rows else False
        if all_checked:
            for r in self._rows: r.cb_var.set(False); r._on_check()
        else:
            for r in self._rows: r.cb_var.set(True); r._on_check()
        self._update_sel_label()

    def _update_sel_label(self):
        n = sum(1 for r in self._rows if r.is_checked())
        total = len(self._rows)
        self.sel_lbl.configure(text=t("sel_n", n=n) if self._rows else "")
        all_on = (n == total and total > 0)
        try:
            self._sel_toggle_btn.configure(
                text=t("sel_none") if all_on else t("sel_all"))
        except: pass
        can = n > 0 and not self._run
        self.start_btn.configure(state="normal" if can else "disabled")

    def _scan(self):
        if not self._src or not os.path.isdir(self._src): return
        mp3s = get_mp3s(self._src)
        dst = self._dst
        ex = get_tracks(dst) if dst and os.path.isdir(dst) else set()
        free = sum(1 for i in range(1, 201) if i not in ex)
        nn = next_free(ex)
        self._mp3s = list(mp3s)
        self.s_mp3.configure(text=str(len(mp3s)))
        self.s_ogg.configure(text=str(len(ex)))
        self.s_next.configure(text=str(nn) if nn else "MAX")
        self.s_free.configure(text=str(free))
        self._rebuild_rows()

    def _build_tmap(self):
        dst = self._dst
        ex = get_tracks(dst) if dst and os.path.isdir(dst) else set()
        cur = next_free(ex); ex2 = set(ex)
        self._tmap = {}
        for mp3 in self._mp3s:
            if cur is None or cur > 200: self._tmap[mp3] = None
            else:
                self._tmap[mp3] = cur; ex2.add(cur); cur = next_free(ex2, cur + 1)

    def _rebuild_rows(self, preserve_checks=None, preserve_statuses=None):
        self._build_tmap()
        for w in self.scroll.winfo_children(): w.destroy()
        self._rows = []
        if not self._mp3s:
            label = t("empty") if not self._src else t("no_mp3")
            el = ctk.CTkLabel(self.scroll, text=label, font=("Segoe UI", 13),
                               text_color=TH("subtext"))
            el.pack(pady=50); self._tw["empty"] = el
            self.start_btn.configure(state="disabled")
            self.sel_lbl.configure(text=""); return
        for i, mp3 in enumerate(self._mp3s):
            tn = self._tmap.get(mp3)
            ts = f"track{tn}.ogg" if tn else "-- (max)"
            idx = i
            r = FileRow(self.scroll, mp3, ts,
                        on_move_up=lambda i=idx: self._move(i, -1),
                        on_move_down=lambda i=idx: self._move(i, 1),
                        on_check_change=self._update_sel_label)
            r.pack(fill="x", padx=6, pady=1)
            if preserve_checks and mp3 in preserve_checks:
                r.cb_var.set(preserve_checks[mp3]); r._on_check()
            if preserve_statuses and mp3 in preserve_statuses:
                r.set_status(preserve_statuses[mp3])
            elif not tn: r.set_status("skipped")
            self._rows.append(r)
        self.prog.set(0); self.timer.reset()
        self.status.configure(text=t("ready"))
        self._update_sel_label()

    def _start(self):
        if self._run: return
        if not self._src or not os.path.isdir(self._src):
            self.status.configure(text="⚠ " + t("src_folder")); return
        if not self._dst or not os.path.isdir(self._dst):
            self.status.configure(text="⚠ " + t("dst_folder")); return
        self._run = True
        jobs = [(mp3, self._tmap[mp3])
                for mp3, row in zip(self._mp3s, self._rows)
                if row.is_checked() and self._tmap.get(mp3)]
        total = len(jobs)
        if not total: self._run = False; return
        log.info(f"Conversion started: {total} files  src={self._src}  dst={self._dst}")
        self.start_btn.configure(state="disabled", text=t("btn_conv"))
        self.timer.start(total)
        threading.Thread(target=self._run_t, args=(jobs,), daemon=True).start()

    def _run_t(self, jobs):
        src = self._src; dst = self._dst
        rows_snapshot = list(self._rows)
        mp3s_snapshot = list(self._mp3s)
        total = len(jobs); done = errors = 0
        for i, (mp3, tn) in enumerate(jobs):
            try: row = rows_snapshot[mp3s_snapshot.index(mp3)]
            except: continue
            self.after(0, row.set_status, "converting")
            inp = os.path.join(src, mp3)
            out = os.path.join(dst, f"track{tn}.ogg")
            res = run_h([FFMPEG, "-n", "-i", inp, "-c:a", "libvorbis", "-q:a", "5", out],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=NO_WINDOW | self._get_priority())
            ok = res.returncode == 0; done += 1; errors += 0 if ok else 1
            if ok:
                log.debug(f"  OK  {mp3} → track{tn}.ogg")
            else:
                log.warning(f"  FAIL  {mp3} (ffmpeg returncode={res.returncode})")
            self.after(0, row.set_status, "done" if ok else "error")
            if ok: self.after(0, row.set_track, f"track{tn}.ogg")
            self.after(0, self.prog.set, done / total)
            self.timer.update_progress(done)
        self.after(0, self._finish, done, errors)

    def _finish(self, done, errors):
        self._run = False; self.timer.stop()
        log.info(f"Conversion finished: {done-errors} ok, {errors} errors")
        self.start_btn.configure(state="normal", text=t("btn_start")); self.prog.set(1)
        self.status.configure(
            text=t("done_all", n=done) if not errors else t("done_part", ok=done-errors, err=errors))
        msg = t("notif_conv_msg", ok=done) if not errors else t("notif_conv_err", ok=done-errors, err=errors)
        threading.Thread(target=notify, args=(t("notif_conv_title"), msg), daemon=True).start()
        save_history_entry({
            "type": "conversion", "date": time.strftime("%Y-%m-%d %H:%M"),
            "count": done - errors, "errors": errors,
            "urls": [self._src]
        })
        self._scan()

class YouTubeTab(ctk.CTkFrame):
    """YouTube download tab. Supports single videos and playlists, with a queue
    system and preview before downloading.
    """

    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._folder = ""; self._run = False
        self._stop = threading.Event(); self._proc = None
        self._proc_lock = threading.Lock()
        self._tw = {}; self._queue = []
        self._build()

    def _build(self):
        br = ctk.CTkFrame(self, fg_color="transparent")
        br.pack(side="bottom", fill="x", pady=(6, 4))
        self.status = ctk.CTkLabel(br, text=t("ready"), font=("Segoe UI", 12),
                                    text_color=TH("subtext"))
        self.status.pack(side="left")
        self.stop_btn = AnimBtn(br, text=t("btn_stop"), variant="danger", width=130,
            height=50, font=("Segoe UI", 13, "bold"), state="disabled", command=self._do_stop)
        self.stop_btn.pack(side="right", padx=(10, 0))
        self.dl_btn = AnimBtn(br, text=t("btn_dl"), variant="accent", width=185,
            height=50, font=("Segoe UI", 14, "bold"), command=self._start)
        self.dl_btn.pack(side="right")
        self._tw["stop"] = self.stop_btn; self._tw["dl"] = self.dl_btn

        self.prog = ctk.CTkProgressBar(self, height=5, fg_color=TH("surface2"),
                                        progress_color=TH("accent"), corner_radius=3)
        self.prog.pack(side="bottom", fill="x", pady=(0, 3)); self.prog.set(0)
        self.timer = TimerBar(self); self.timer.pack(side="bottom", fill="x", pady=(0, 5))

        url_card = card(self); url_card.pack(fill="x", pady=(0, 8))
        ui = ctk.CTkFrame(url_card, fg_color="transparent"); ui.pack(fill="x", padx=18, pady=12)
        ul = ctk.CTkLabel(ui, text=t("url_lbl"), font=("Segoe UI", 10, "bold"),
                           text_color=TH("subtext"))
        ul.pack(anchor="w"); self._tw["url_lbl"] = ul

        url_row = ctk.CTkFrame(ui, fg_color="transparent"); url_row.pack(fill="x", pady=(5, 0))
        self.url_e = ctk.CTkEntry(url_row, placeholder_text="https://youtube.com/watch?v=...",
            font=("Segoe UI", 13), fg_color=TH("surface2"), border_color=TH("border"),
            text_color=TH("text"), height=42, border_width=1)
        self.url_e.pack(side="left", fill="x", expand=True, padx=(0, 10))

        fetch_btn = AnimBtn(url_row, text=t("preview_btn"), width=130, height=42,
            font=("Segoe UI", 11, "bold"), command=self._fetch_preview)
        fetch_btn.pack(side="right", padx=(0, 8)); self._tw["preview_btn"] = fetch_btn

        add_btn = AnimBtn(url_row, text=t("queue_add"), width=150, height=42,
            font=("Segoe UI", 11, "bold"), variant="accent", command=self._add_to_queue)
        add_btn.pack(side="right"); self._tw["queue_add"] = add_btn

        self._preview_card = ctk.CTkFrame(ui, fg_color=TH("surface2"), corner_radius=8,
                                           border_width=1, border_color=TH("border"))
        self._preview_card.pack(fill="x", pady=(8, 0))
        self._preview_lbl = ctk.CTkLabel(self._preview_card, text=t("preview_none"),
            font=("Segoe UI", 11), text_color=TH("subtext"), justify="left", anchor="w")
        self._preview_lbl.pack(fill="x", padx=14, pady=8)

        opts = card(self); opts.pack(fill="x", pady=(0, 8))
        oi = ctk.CTkFrame(opts, fg_color="transparent"); oi.pack(fill="x", padx=18, pady=12)
        fl = ctk.CTkLabel(oi, text=t("dst_lbl"), font=("Segoe UI", 10, "bold"),
                           text_color=TH("subtext"))
        fl.pack(anchor="w"); self._tw["dst_lbl"] = fl
        frow = ctk.CTkFrame(oi, fg_color="transparent"); frow.pack(fill="x", pady=(5, 0))
        self.fe = ctk.CTkEntry(frow, placeholder_text="...", font=("Segoe UI", 13),
            fg_color=TH("surface2"), border_color=TH("border"),
            text_color=TH("text"), height=42, border_width=1)
        self.fe.pack(side="left", fill="x", expand=True, padx=(0, 10))
        bb = AnimBtn(frow, text=t("browse"), width=100, height=42,
                     font=("Segoe UI", 12, "bold"), command=self._browse)
        bb.pack(side="right"); self._tw["browse"] = bb
        self._auto = ctk.CTkLabel(oi, text="", font=("Segoe UI", 10),
                                   text_color=TH("subtext"))
        self._auto.pack(anchor="w", pady=(4, 0))

        swr = ctk.CTkFrame(oi, fg_color=TH("surface2"), corner_radius=8,
                            border_width=1, border_color=TH("border"))
        swr.pack(fill="x", pady=(8, 0))
        swi = ctk.CTkFrame(swr, fg_color="transparent"); swi.pack(fill="x", padx=14, pady=8)
        self.sw_lbl = ctk.CTkLabel(swi, text=t("sw_video"), font=("Segoe UI", 12),
                                    text_color=TH("text"))
        self.sw_lbl.pack(side="left")
        self.pl_sw = ctk.CTkSwitch(swi, text="", width=46,
            button_color=TH("accent"), button_hover_color=TH("acc_hi"),
            progress_color=TH("accent"), fg_color=TH("border"),
            command=self._toggle_pl)
        self.pl_sw.pack(side="right")

        split = ctk.CTkFrame(self, fg_color="transparent"); split.pack(fill="both", expand=True)
        split.columnconfigure(0, weight=1); split.columnconfigure(1, weight=2)
        split.rowconfigure(0, weight=1)

        qp = ctk.CTkFrame(split, fg_color="transparent")
        qp.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        qh = ctk.CTkFrame(qp, fg_color="transparent"); qh.pack(fill="x", pady=(0, 5))
        ql = ctk.CTkLabel(qh, text=t("queue_label"), font=("Segoe UI", 10, "bold"),
                           text_color=TH("subtext"))
        ql.pack(side="left"); self._tw["queue_lbl"] = ql
        clr_btn = AnimBtn(qh, text=t("queue_clear"), width=80, height=26,
            font=("Segoe UI", 10, "bold"), command=self._clear_queue)
        clr_btn.pack(side="right"); self._tw["queue_clr"] = clr_btn
        qc = card(qp); qc.pack(fill="both", expand=True)
        self._queue_scroll = ctk.CTkScrollableFrame(qc, fg_color="transparent",
                                                     scrollbar_button_color=TH("border"))
        self._queue_scroll.pack(fill="both", expand=True, padx=8, pady=8)
        self._queue_empty_lbl = ctk.CTkLabel(self._queue_scroll, text=t("queue_empty"),
            font=("Segoe UI", 11), text_color=TH("subtext"))
        self._queue_empty_lbl.pack(pady=30)

        lp = ctk.CTkFrame(split, fg_color="transparent")
        lp.grid(row=0, column=1, sticky="nsew")
        ll = ctk.CTkLabel(lp, text=t("log_lbl"), font=("Segoe UI", 10, "bold"),
                           text_color=TH("subtext"))
        ll.pack(anchor="w", pady=(0, 5)); self._tw["log_lbl"] = ll
        lc = card(lp); lc.pack(fill="both", expand=True)
        self.log = ctk.CTkTextbox(lc, font=("Consolas", 11), fg_color="transparent",
                                   text_color=TH("text"), wrap="word", state="normal")
        self.log.pack(fill="both", expand=True, padx=8, pady=8)
        self._logi(t("log_hint"))

        self._init_folder()

    def _init_folder(self):
        cfg = load_config(); s = cfg.get("folder", "")
        if s and os.path.isdir(s): self._setf(s, t("auto_saved")); return
        f, _ = find_mwc_radio()
        if f: self._setf(f, t("auto_found"))
        else: self._auto.configure(text=t("auto_miss"), text_color=TH("subtext"))

    def _setf(self, path, msg="", color=None):
        self._folder = path; self.fe.delete(0, "end"); self.fe.insert(0, path)
        self._auto.configure(text=msg, text_color=color or TH("success"))

    def retranslate(self):
        self._tw["url_lbl"].configure(text=t("url_lbl"))
        self._tw["dst_lbl"].configure(text=t("dst_lbl"))
        self._tw["browse"].configure(text=t("browse"))
        self._tw["log_lbl"].configure(text=t("log_lbl"))
        self._tw["preview_btn"].configure(text=t("preview_btn"))
        self._tw["queue_add"].configure(text=t("queue_add"))
        self._tw["queue_lbl"].configure(text=t("queue_label"))
        self._tw["queue_clr"].configure(text=t("queue_clear"))
        self.status.configure(text=t("ready"))
        if not self._run:
            self.dl_btn.configure(text=t("btn_dl"))
            self.stop_btn.configure(text=t("btn_stop"))
        self._toggle_pl(); self.timer.retranslate()
        self._rebuild_queue_ui()

    def _toggle_pl(self):
        self.sw_lbl.configure(text=t("sw_playlist") if self.pl_sw.get() else t("sw_video"))

    def _browse(self):
        f = filedialog.askdirectory()
        if f: save_config({"folder": f}); self._setf(f, t("auto_saved"))


    def _fetch_preview(self):
        url = self.url_e.get().strip()
        if not url: return
        self._preview_lbl.configure(text="⟳  " + t("fetching"), text_color=TH("subtext"))
        threading.Thread(target=self._do_fetch_preview, args=(url,), daemon=True).start()

    def _do_fetch_preview(self, url):
        try:
            res = subprocess.run(
                [YTDLP, "--no-playlist", "--skip-download",
                 "--print", "title", "--print", "duration_string", url],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", creationflags=NO_WINDOW, timeout=15)
            lines = [x.strip() for x in res.stdout.strip().splitlines() if x.strip()]
            if len(lines) >= 2:
                title, dur = lines[0], lines[1]
                info = f"▶  {title}\n⏱  {dur}"
            elif len(lines) == 1:
                info = f"▶  {lines[0]}"
            else:
                info = "⚠  " + t("log_fail")
            color = TH("text") if lines else TH("error")
            def _set_preview(txt=info, col=color):
                try: self._preview_lbl.configure(text=txt, text_color=col)
                except: pass
            self.after(0, _set_preview)
        except Exception as e:
            err = str(e)
            def _set_err(msg=err):
                try: self._preview_lbl.configure(text=f"⚠  {msg}", text_color=TH("error"))
                except: pass
            self.after(0, _set_err)


    def _add_to_queue(self):
        url = self.url_e.get().strip()
        if not url or url in self._queue: return
        self._queue.append(url)
        self.url_e.delete(0, "end")
        self._preview_lbl.configure(text=t("preview_none"), text_color=TH("subtext"))
        self._rebuild_queue_ui()

    def _remove_from_queue(self, url):
        if url in self._queue: self._queue.remove(url)
        self._rebuild_queue_ui()

    def _clear_queue(self):
        self._queue.clear(); self._rebuild_queue_ui()

    def _rebuild_queue_ui(self):
        for w in self._queue_scroll.winfo_children(): w.destroy()
        if not self._queue:
            ctk.CTkLabel(self._queue_scroll, text=t("queue_empty"),
                font=("Segoe UI", 11), text_color=TH("subtext")).pack(pady=30)
            return
        for i, url in enumerate(self._queue):
            row = ctk.CTkFrame(self._queue_scroll, fg_color=TH("surface2"),
                                corner_radius=6, border_width=1, border_color=TH("border"))
            row.pack(fill="x", pady=2, padx=2)
            short = url if len(url) <= 38 else url[:35] + "..."
            ctk.CTkLabel(row, text=f"{i+1}.  {short}", font=("Segoe UI", 10),
                          text_color=TH("text"), anchor="w").pack(side="left", padx=10, pady=6, fill="x", expand=True)
            ctk.CTkButton(row, text="✕", width=28, height=28, font=("Segoe UI", 11),
                fg_color="transparent", hover_color=TH("error"), text_color=TH("subtext"),
                border_width=0, corner_radius=6,
                command=lambda u=url: self._remove_from_queue(u)).pack(side="right", padx=4)


    def _logi(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _log(self, msg): self.after(0, self._logi, msg)


    def _start(self):
        urls = list(self._queue) if self._queue else []
        if not urls:
            url = self.url_e.get().strip()
            if url: urls = [url]
        folder = self._folder
        if not urls: self._log(t("no_url")); return
        if not folder or not os.path.isdir(folder): self._log(t("no_folder")); return
        if self._run: return
        self._run = True; self._stop.clear()
        self.after(0, lambda: self.dl_btn.configure(state="disabled", text=t("btn_dling")))
        self.after(0, lambda: self.stop_btn.configure(state="normal"))
        self.prog.set(0); self.log.configure(state="normal"); self.log.delete("1.0", "end")
        pl = bool(self.pl_sw.get())
        threading.Thread(target=self._run_t, args=(urls, folder, pl), daemon=True).start()

    def _do_stop(self):
        if not self._run: return
        self._stop.set()
        with self._proc_lock:
            if self._proc:
                try: self._proc.terminate()
                except: pass
        self._log(t("stopped")); self.after(0, self._done, True)

    def _run_t(self, urls, folder, pl):
        total_ok = total_err = 0
        total_vids = len(urls)
        self.after(0, self.timer.start, total_vids)

        for qi, url in enumerate(urls):
            if self._stop.is_set(): break
            log.info(f"YouTube download [{qi+1}/{total_vids}]: {url}")
            self._log(f"\n{'─'*40}")
            self._log(f"[{qi+1}/{total_vids}]  {url}")
            self._log(t("fetching"))

            flag = "--no-playlist" if not pl else "--flat-playlist"
            info = subprocess.run([YTDLP, flag, "--print", "title", url],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", creationflags=NO_WINDOW)
            titles = [x.strip() for x in info.stdout.strip().splitlines() if x.strip()]
            if not pl: titles = titles[:1]
            count = len(titles)
            self._log(t("found_n", n=count) + "\n")
            self.after(0, self.timer.set_total, total_vids)

            ex = get_tracks(folder); sn = next_free(ex)
            if sn is None: self._log(t("all_used")); break

            cur = sn
            for i, title in enumerate(titles):
                if self._stop.is_set(): break
                if cur is None or cur > 200: self._log(t("max")); break
                tpl = os.path.join(folder, f"track{cur}")
                exp = os.path.join(folder, f"track{cur}.ogg")
                self._log(f"  ↓  {title[:55]}{'...' if len(title)>55 else ''}")
                self._log(f"     → track{cur}.ogg")
                cmd = [YTDLP, "-x", "--audio-format", "vorbis", "--audio-quality", "5",
                       "--ffmpeg-location", BIN_DIR, "-o", tpl,
                       "--no-playlist" if not pl else "--yes-playlist"]
                if pl and count > 1: cmd += ["--playlist-items", str(i+1)]
                cmd.append(url)
                try:
                    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
                    with self._proc_lock: self._proc = proc
                    proc.wait()
                    ok = proc.returncode == 0 and os.path.isfile(exp)
                except: ok = False
                finally:
                    with self._proc_lock: self._proc = None
                if self._stop.is_set(): break
                if ok:
                    log.debug(f"  OK  {title[:60]} → track{cur}.ogg")
                    self._log(f"     {t('log_ok')}\n"); total_ok += 1
                else:
                    log.warning(f"  FAIL  {title[:60]} (yt-dlp error)")
                    self._log(f"     {t('log_fail')}\n"); total_err += 1
                cur = next_free(get_tracks(folder), cur + 1)
                self.timer.update_progress(qi + 1)

        self._log(f"\n{'─'*40}")
        self._log(t("summary", ok=total_ok, err=total_err))
        log.info(f"YouTube session done: {total_ok} ok, {total_err} errors")
        if not self._stop.is_set():
            save_history_entry({
                "type": "download", "date": time.strftime("%Y-%m-%d %H:%M"),
                "count": total_ok, "errors": total_err,
                "urls": urls[:5]
            })
            msg = t("notif_dl_msg", ok=total_ok) if not total_err else t("notif_dl_err", ok=total_ok, err=total_err)
            threading.Thread(target=notify, args=(t("notif_dl_title"), msg), daemon=True).start()
        self.after(0, self._done)

    def _done(self, stopped=False):
        self._run = False; self.timer.stop()
        self.after(0, lambda: self.dl_btn.configure(state="normal", text=t("btn_dl")))
        self.after(0, lambda: self.stop_btn.configure(state="disabled"))
        if not stopped: self.after(0, lambda: self.prog.set(1.0))
        if not stopped and self._queue:
            self.after(0, self._clear_queue)

class HistoryTab(ctk.CTkFrame):
    """Displays a log of past conversions and downloads with timestamps."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._tw = {}; self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent"); hdr.pack(fill="x", pady=(0, 8))
        hl = ctk.CTkLabel(hdr, text="HISTORY", font=("Segoe UI", 10, "bold"),
                           text_color=TH("subtext"))
        hl.pack(side="left"); self._tw["title"] = hl
        clr = AnimBtn(hdr, text=t("history_clear"), width=150, height=32,
                       font=("Segoe UI", 11, "bold"), variant="danger", command=self._clear)
        clr.pack(side="right"); self._tw["clear_btn"] = clr

        lc = card(self); lc.pack(fill="both", expand=True)
        self.scroll = ctk.CTkScrollableFrame(lc, fg_color="transparent",
                                              scrollbar_button_color=TH("border"))
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh()

    def refresh(self):
        for w in self.scroll.winfo_children(): w.destroy()
        history = load_history()
        if not history:
            ctk.CTkLabel(self.scroll, text=t("history_empty"),
                font=("Segoe UI", 13), text_color=TH("subtext")).pack(pady=50)
            return
        for entry in history:
            row = ctk.CTkFrame(self.scroll, fg_color=TH("surface2"), corner_radius=8,
                                border_width=1, border_color=TH("border"))
            row.pack(fill="x", pady=3, padx=2)
            ri = ctk.CTkFrame(row, fg_color="transparent"); ri.pack(fill="x", padx=14, pady=10)
            kind = t("hist_conv") if entry.get("type") == "conversion" else t("hist_dl")
            date = entry.get("date", "")
            ok   = entry.get("count", 0)
            err  = entry.get("errors", 0)
            icon = "🎵" if entry.get("type") == "conversion" else "⬇"
            ctk.CTkLabel(ri, text=f"{icon}  {kind}",
                font=("Segoe UI", 12, "bold"), text_color=TH("accent")).pack(anchor="w")
            ctk.CTkLabel(ri, text=f"{date}  ·  {ok} ok" + (f"  ·  {err} failed" if err else ""),
                font=("Segoe UI", 10), text_color=TH("subtext")).pack(anchor="w")
            urls = entry.get("urls", [])
            if urls:
                ctk.CTkLabel(ri, text=urls[0][:60] + ("..." if len(urls[0]) > 60 else ""),
                    font=("Consolas", 9), text_color=TH("muted")).pack(anchor="w", pady=(2, 0))

    def _clear(self):
        clear_history(); self.refresh()

    def retranslate(self):
        self._tw["clear_btn"].configure(text=t("history_clear"))
        self.refresh()

class SettingsTab(ctk.CTkFrame):
    """Application settings: theme, accent color, language, font size,
    update checking, and tool management.
    """

    def __init__(self, master, callbacks=None, **kw):
        kw.pop("callbacks", None)
        super().__init__(master, fg_color="transparent", **kw)
        self._cb = callbacks or {}
        self._tw = {}
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                         scrollbar_button_color=TH("border"))
        scroll.pack(fill="both", expand=True)

        ap_lbl = ctk.CTkLabel(scroll, text=t("settings_appear"),
            font=("Segoe UI",10,"bold"), text_color=TH("subtext"))
        ap_lbl.pack(anchor="w", pady=(16,4)); self._tw["settings_appear"] = ap_lbl
        app_card = card(scroll); app_card.pack(fill="x")

        r1 = ctk.CTkFrame(app_card, fg_color="transparent"); r1.pack(fill="x", padx=18, pady=(14,8))
        th_lbl = ctk.CTkLabel(r1, text=t("settings_theme"), font=("Segoe UI",12),
                               text_color=TH("text"), anchor="w")
        th_lbl.pack(side="left"); self._tw["settings_theme"] = th_lbl
        tf = ctk.CTkFrame(r1, fg_color=TH("surface2"), corner_radius=8,
                           border_width=1, border_color=TH("border"))
        tf.pack(side="right")
        tfi = ctk.CTkFrame(tf, fg_color="transparent"); tfi.pack(padx=10, pady=6)
        self._th_lbl = ctk.CTkLabel(tfi,
            text=t("dark_th") if _theme=="dark" else t("light_th"),
            font=("Segoe UI",11), text_color=TH("subtext"))
        self._th_lbl.pack(side="left", padx=(0,8))
        self._th_sw = ctk.CTkSwitch(tfi, text="", width=44, height=22,
            button_color=TH("accent"), button_hover_color=TH("acc_hi"),
            progress_color=TH("accent"), fg_color=TH("border"),
            command=lambda: self._cb.get("toggle_theme", lambda: None)())
        self._th_sw.pack(side="left")
        if _theme == "light": self._th_sw.select()

        ctk.CTkFrame(app_card, height=1, fg_color=TH("border")).pack(fill="x", padx=12)

        r2 = ctk.CTkFrame(app_card, fg_color="transparent"); r2.pack(fill="x", padx=18, pady=10)
        ac_lbl = ctk.CTkLabel(r2, text=t("settings_accent"), font=("Segoe UI",12),
                               text_color=TH("text"), anchor="w")
        ac_lbl.pack(side="left"); self._tw["settings_accent"] = ac_lbl
        sw = ctk.CTkFrame(r2, fg_color="transparent"); sw.pack(side="right")
        for hex_color, _ in ACCENT_PRESETS:
            is_active = hex_color == TH("accent")
            ctk.CTkButton(sw, text="", width=28, height=28,
                fg_color=hex_color, hover_color=hex_color, corner_radius=14,
                border_width=2 if is_active else 0,
                border_color=TH("text") if is_active else hex_color,
                command=lambda h=hex_color: self._cb.get("set_accent", lambda h: None)(h)
            ).pack(side="left", padx=2)

        ctk.CTkFrame(app_card, height=1, fg_color=TH("border")).pack(fill="x", padx=12)

        r3 = ctk.CTkFrame(app_card, fg_color="transparent"); r3.pack(fill="x", padx=18, pady=10)
        la_lbl = ctk.CTkLabel(r3, text=t("settings_lang"), font=("Segoe UI",12),
                               text_color=TH("text"), anchor="w")
        la_lbl.pack(side="left"); self._tw["settings_lang"] = la_lbl
        lf = ctk.CTkFrame(r3, fg_color="transparent"); lf.pack(side="right")
        self._lang_btns = {}
        for code, label in LANG_OPTIONS:
            active = code == _lang
            btn = ctk.CTkButton(lf, text=label, width=130, height=30,
                font=("Segoe UI",11),
                fg_color=TH("accent") if active else TH("surface2"),
                hover_color=TH("acc_hi") if active else TH("surface3"),
                text_color=TH("bg") if active else TH("text"),
                corner_radius=6, border_width=1,
                border_color=TH("acc_hi") if active else TH("border"),
                command=lambda c=code: self._cb.get("set_lang", lambda c: None)(c))
            btn.pack(pady=2)
            self._lang_btns[code] = btn

        ctk.CTkFrame(app_card, height=1, fg_color=TH("border")).pack(fill="x", padx=12)

        r4 = ctk.CTkFrame(app_card, fg_color="transparent"); r4.pack(fill="x", padx=18, pady=(10,14))
        fn_lbl = ctk.CTkLabel(r4, text=t("settings_font"), font=("Segoe UI",12),
                               text_color=TH("text"), anchor="w")
        fn_lbl.pack(side="left"); self._tw["settings_font"] = fn_lbl
        font_seg = ctk.CTkSegmentedButton(r4,
            values=[t("font_small"), t("font_normal"), t("font_large")],
            selected_color=TH("accent"), selected_hover_color=TH("acc_hi"),
            unselected_color=TH("surface2"), unselected_hover_color=TH("surface3"),
            fg_color=TH("surface2"), text_color=TH("text"),
            font=("Segoe UI",11), command=self._set_font)
        font_seg.pack(side="right")
        saved = load_config().get("font_size", "normal")
        font_seg.set(t(f"font_{saved}"))
        self._font_seg = font_seg

        app_lbl = ctk.CTkLabel(scroll, text=t("settings_app"),
            font=("Segoe UI",10,"bold"), text_color=TH("subtext"))
        app_lbl.pack(anchor="w", pady=(16,4)); self._tw["settings_app"] = app_lbl
        info_card = card(scroll); info_card.pack(fill="x")

        vr = ctk.CTkFrame(info_card, fg_color="transparent"); vr.pack(fill="x", padx=18, pady=(14,8))
        ctk.CTkLabel(vr, text="Version", font=("Segoe UI",12), text_color=TH("text")).pack(side="left")
        ctk.CTkLabel(vr, text=f"MTO v{APP_VERSION}",
            font=("Consolas",12,"bold"), text_color=TH("accent")).pack(side="right")

        ctk.CTkFrame(info_card, height=1, fg_color=TH("border")).pack(fill="x", padx=12)

        ur = ctk.CTkFrame(info_card, fg_color="transparent"); ur.pack(fill="x", padx=18, pady=8)
        self._upd_lbl = ctk.CTkLabel(ur, text=t("check_updates"),
            font=("Segoe UI",12), text_color=TH("text"))
        self._upd_lbl.pack(side="left"); self._tw["check_updates"] = self._upd_lbl
        AnimBtn(ur, text=t("check_updates"), width=160, height=34,
            font=("Segoe UI",11,"bold"), command=self._check_updates).pack(side="right")

        ctk.CTkFrame(info_card, height=1, fg_color=TH("border")).pack(fill="x", padx=12)

        rr = ctk.CTkFrame(info_card, fg_color="transparent"); rr.pack(fill="x", padx=18, pady=8)
        ctk.CTkLabel(rr, text=t("reset_settings"), font=("Segoe UI",12),
                      text_color=TH("text")).pack(side="left")
        AnimBtn(rr, text=t("reset_settings"), width=160, height=34, variant="danger",
            font=("Segoe UI",11,"bold"), command=self._reset).pack(side="right")

        tl = ctk.CTkLabel(scroll, text=t("settings_tools"),
            font=("Segoe UI",10,"bold"), text_color=TH("subtext"))
        tl.pack(anchor="w", pady=(16,4)); self._tw["settings_tools"] = tl
        tools_card = card(scroll); tools_card.pack(fill="x", pady=(0,20))
        unr = ctk.CTkFrame(tools_card, fg_color="transparent"); unr.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(unr, text=t("uninstall_tools"), font=("Segoe UI",12),
                      text_color=TH("text")).pack(side="left")
        self._unin_btn = AnimBtn(unr, text=t("uninstall_tools"), width=200, height=34,
            variant="danger", font=("Segoe UI",11,"bold"),
            command=self._uninstall_tools)
        self._unin_btn.pack(side="right")
        self._unin_status = ctk.CTkLabel(tools_card, text="",
            font=("Segoe UI",10), text_color=TH("success"))
        self._unin_status.pack(pady=(0,10))

    def _set_font(self, val):
        sizes = {t("font_small"):"small", t("font_normal"):"normal", t("font_large"):"large"}
        key = sizes.get(val, "normal")
        save_config({"font_size": key})
        scales = {"small": 0.9, "normal": 1.0, "large": 1.15}
        ctk.set_widget_scaling(scales.get(key, 1.0))
        saved_tab = None
        try: saved_tab = self.winfo_toplevel()._tabs_ref.get()
        except: pass
        try:
            self.winfo_toplevel()._main()
            if saved_tab:
                st = saved_tab
                self.winfo_toplevel().after(200, lambda: self.winfo_toplevel()._tabs_ref.set(st))
        except: pass

    def _check_updates(self):
        self._upd_lbl.configure(text=t("fetching"), text_color=TH("subtext"))
        def _do():
            ver, url, changelog = check_for_update()
            if ver and url:
                self.after(0, lambda: self._cb.get("show_changelog",
                    lambda v,u,ch: None)(ver, url, changelog))
                self.after(0, lambda: self._upd_lbl.configure(
                    text=t("update_avail", ver=ver), text_color=TH("accent")))
            else:
                self.after(0, lambda: self._upd_lbl.configure(
                    text=t("up_to_date"), text_color=TH("success")))
        threading.Thread(target=_do, daemon=True).start()

    def _reset(self):
        save_config({"lang":"en","theme":"dark","accent":None,"font_size":"normal",
                     "tutorial_seen":False,"conv_speed":1})
        self._cb.get("toggle_theme", lambda: None)()

    def _uninstall_tools(self):
        try:
            if os.path.exists(BIN_DIR): shutil.rmtree(BIN_DIR)
            self._unin_status.configure(text=t("uninstall_done"), text_color=TH("success"))
            self._unin_btn.configure(state="disabled")
        except Exception as e:
            self._unin_status.configure(text=f"Error: {e}", text_color=TH("error"))

    def retranslate(self):
        for key, w in self._tw.items():
            try: w.configure(text=t(key))
            except: pass
        try: self._th_lbl.configure(text=t("dark_th") if _theme=="dark" else t("light_th"))
        except: pass


class App(ctk.CTk):
    """Main application window. Manages splash screen, setup wizard, tabs,
    tray icon, auto-updater, and theme/language switching.
    """

    def __init__(self):
        super().__init__()
        cfg=load_config()
        global _lang,_theme
        _lang=cfg.get("lang","en")
        saved_accent = cfg.get("accent", None)
        apply_theme(cfg.get("theme","dark"), accent=saved_accent)
        font_scales = {"small": 0.9, "normal": 1.0, "large": 1.15}
        ctk.set_widget_scaling(font_scales.get(cfg.get("font_size","normal"), 1.0))
        self.title("MTO — Mp3ToOgg"); self.geometry("940x800"); self.minsize(740,660)
        self.configure(fg_color=TH("bg"))
        global _APP_INSTANCE
        _APP_INSTANCE = self
        _setup_logging()
        log.info(f"MTO v{APP_VERSION} starting — theme={_theme} lang={_lang}")
        self._ct=None; self._yt=None
        self._tray_icon = None
        if deps_ok():
            self._splash()
        else:
            self._setup_then_main()

    def _setup_then_main(self):
        self.after(100, self._do_setup)

    def _do_setup(self):
        self.withdraw()
        setup_win = ctk.CTkToplevel()
        setup_win.title("MTO — Setup")
        setup_win.geometry("700x660")
        setup_win.configure(fg_color=TH("bg"))
        setup_win.resizable(False, False)
        setup_win.protocol("WM_DELETE_WINDOW", lambda: [setup_win.destroy(), self.destroy()])
        try:
            import os as _os
            ico = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo.ico")
            if _os.path.isfile(ico): setup_win.iconbitmap(ico)
        except: pass

        def on_setup_done():
            setup_win.destroy()
            self.deiconify()
            self._main()

        sf = SetupFrame(setup_win, on_done=on_setup_done)
        sf.pack(fill="both", expand=True)

    def _launch_after_setup(self):
        for w in self.winfo_children():
            w.destroy()
        self._main()

    def _splash(self):
        self.attributes("-alpha",0.0)
        sp=ctk.CTkFrame(self,fg_color=TH("bg"),corner_radius=0)
        sp.place(relx=0,rely=0,relwidth=1,relheight=1)
        box=ctk.CTkFrame(sp,fg_color="transparent"); box.place(relx=0.5,rely=0.46,anchor="center")
        ctk.CTkLabel(box,text="MTO",font=("Segoe UI",44,"bold"),text_color=TH("accent")).pack()
        ctk.CTkLabel(box,text=t("app_sub"),font=("Segoe UI",14),text_color=TH("subtext")).pack(pady=(6,40))
        bar=ctk.CTkProgressBar(box,width=320,height=4,fg_color=TH("border"),
            progress_color=TH("accent"),corner_radius=2); bar.pack(); bar.set(0)
        slbl=ctk.CTkLabel(box,text="",font=("Consolas",11),text_color=TH("subtext"))
        slbl.pack(pady=(10,0))
        steps=["Ladataan...","Valmistellaan...","Käynnistetään..."]

        def fi(a=0.0):
            a=min(a+0.07,1.0)
            try: self.attributes("-alpha",a)
            except: pass
            if a<1.0: self.after(14,lambda: fi(a))
            else: fb(0.0)

        def fb(p=0.0):
            p=min(p+0.011,1.0)
            try: bar.set(p)
            except: pass
            idx=min(int(p*(len(steps))),len(steps)-1)
            try: slbl.configure(text=steps[idx])
            except: pass
            if p<1.0: self.after(14,lambda: fb(p))
            else: self.after(220,fo)

        def fo(a=1.0):
            a=max(a-0.1,0.0)
            try: self.attributes("-alpha",a)
            except: pass
            if a>0.0: self.after(12,lambda: fo(a))
            else:
                try: sp.destroy()
                except: pass
                self.update_idletasks()
                if deps_ok():
                    self._main()
                else:
                    self._main_frame = ctk.CTkFrame(self, fg_color=TH("bg"))
                    self._main_frame.pack(fill="both", expand=True)
                    SetupFrame(self._main_frame, on_done=lambda: [
                        self._main_frame.destroy(),
                        setattr(self, "_main_frame", None),
                        self._main()])
                fback(0.0)

        def fback(a=0.0):
            a=min(a+0.1,1.0)
            try: self.attributes("-alpha",a)
            except: pass
            if a<1.0: self.after(12,lambda: fback(a))

        self.after(180,lambda: fi())
        try:
            import os as _os
            ico = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo.ico")
            if _os.path.isfile(ico):
                self.iconbitmap(ico)
        except: pass

    def _main(self):
        try: self.attributes("-alpha", 1.0)
        except: pass
        try: self.deiconify()
        except: pass
        for w in self.winfo_children(): w.destroy()
        self.configure(fg_color=TH("bg"))

        hdr=ctk.CTkFrame(self,fg_color=TH("surface"),corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkFrame(hdr,height=2,fg_color=TH("accent"),corner_radius=0).pack(side="bottom",fill="x")
        hi=ctk.CTkFrame(hdr,fg_color="transparent"); hi.pack(fill="x",padx=26,pady=14)

        ctk.CTkLabel(hi,text="MTO",font=("Segoe UI",26,"bold"),text_color=TH("accent")).pack(side="left")
        self._sub=ctk.CTkLabel(hi,text=t("app_sub"),font=("Segoe UI",12),text_color=TH("subtext"))
        self._sub.pack(side="left",padx=(14,0),pady=(12,0))

        ctk.CTkLabel(hi, text=f"v{APP_VERSION}",
            font=("Segoe UI",10), text_color=TH("subtext")).pack(side="right", padx=(0,4))
        self._accent_popup = None
        self._dropdown_visible = False

        self._update_bar = ctk.CTkFrame(self, fg_color=TH("surface"),
            corner_radius=10, border_width=1, border_color=TH("accent"))
        inner_bar = ctk.CTkFrame(self._update_bar, fg_color="transparent")
        inner_bar.pack(padx=12, pady=8)
        ctk.CTkLabel(inner_bar, text="🔔", font=("Segoe UI",14),
            text_color=TH("accent")).pack(side="left", padx=(0,8))
        self._update_bar_lbl = ctk.CTkLabel(inner_bar, text="",
            font=("Segoe UI",11,"bold"), text_color=TH("text"))
        self._update_bar_lbl.pack(side="left", padx=(0,10))
        self._update_bar_btn = AnimBtn(inner_bar, text=t("update_btn"),
            variant="accent", width=160, height=32,
            font=("Segoe UI",10,"bold"))
        self._update_bar_btn.pack(side="left")

        footer = ctk.CTkFrame(self, fg_color=TH("surface2"), corner_radius=0,
                               border_width=0)
        footer.pack(side="bottom", fill="x")
        ctk.CTkFrame(footer, height=1, fg_color=TH("border"), corner_radius=0).pack(fill="x")
        ctk.CTkLabel(footer,
            text=f"© {time.strftime('%Y')} @MorkulaArttu  ·  All rights reserved  ·  MTO v{APP_VERSION}",
            font=("Segoe UI", 10), text_color=TH("subtext")).pack(pady=5)

        tabs=ctk.CTkTabview(self,fg_color=TH("bg"),
            segmented_button_fg_color=TH("surface"),
            segmented_button_selected_color=TH("accent"),
            segmented_button_selected_hover_color=TH("acc_hi"),
            segmented_button_unselected_color=TH("surface"),
            segmented_button_unselected_hover_color=TH("surface2"),
            text_color=TH("text"),text_color_disabled=TH("subtext"))
        tabs.pack(fill="both",expand=True,padx=22,pady=(14,22))
        tabs.add(t("tab_conv")); tabs.add(t("tab_yt"))
        tabs.add(t("history_tab")); tabs.add(t("settings_tab"))
        self._ct = ConverterTab(tabs.tab(t("tab_conv"))); self._ct.pack(fill="both",expand=True)
        self._yt = YouTubeTab(tabs.tab(t("tab_yt"))); self._yt.pack(fill="both",expand=True)
        self._ht = HistoryTab(tabs.tab(t("history_tab"))); self._ht.pack(fill="both",expand=True)
        self._st = SettingsTab(tabs.tab(t("settings_tab")), callbacks={
            "toggle_theme":  self._toggle_theme,
            "set_accent":    self._set_accent,
            "set_lang":      self._set_lang_direct,
            "show_changelog":self._show_changelog,
        })
        self._st.pack(fill="both", expand=True)
        self._tabs_ref = tabs
        tabs.configure(command=self._on_tab_change)

        if not hasattr(self, "_tray_icon") or self._tray_icon is None:
            self._tray_icon = None
            if HAS_TRAY: self.after(500, self._init_tray)

        self.after(2000, lambda: threading.Thread(target=self._check_update, daemon=True).start())

        cfg = load_config()
        if not cfg.get("tutorial_seen", False):
            self.after(600, self._start_tutorial)

    def _start_tutorial(self):
        TutorialOverlay(
            root=self,
            get_widget_cb=self._get_tutorial_widget,
            on_done=self._tutorial_done
        )

    def _get_tutorial_widget(self, step_id):
        """Return the widget to highlight for each tutorial step."""
        try:
            if step_id == "tut1":
                return self._tabs_ref
            elif step_id == "tut2":
                return self._tabs_ref
            elif step_id == "tut3":
                if self._ct: return self._ct.src_entry
            elif step_id == "tut4":
                if self._ct: return self._ct.start_btn
            elif step_id == "tut5":
                if self._yt: return self._yt.url_e
        except: pass
        return None

    def _tutorial_done(self):
        save_config({"tutorial_seen": True})

    def _set_lang_direct(self, code):
        log.info(f"Language changed: {code}")
        global _lang; _lang = code; save_config({"lang": code})
        self._sub.configure(text=t("app_sub"))
        if self._ct: self._ct.retranslate()
        if self._yt: self._yt.retranslate()
        if hasattr(self,"_ht") and self._ht: self._ht.retranslate()
        if hasattr(self,"_st") and self._st:
            self._st.retranslate()
            for lcode, btn in (self._st._lang_btns if hasattr(self._st, "_lang_btns") else {}).items():
                active = lcode == code
                try:
                    btn.configure(
                        fg_color=TH("accent") if active else TH("surface2"),
                        hover_color=TH("acc_hi") if active else TH("surface3"),
                        text_color=TH("bg") if active else TH("text"),
                        border_color=TH("acc_hi") if active else TH("border"))
                except: pass
        if hasattr(self,"_st") and self._st: self._st.retranslate()

    def _set_accent(self, hex_color):
        apply_theme(_theme, accent=hex_color)
        save_config({"accent": hex_color})
        saved_tab = None
        try: saved_tab = self._tabs_ref.get()
        except: pass
        if hasattr(self,"_tray_icon") and self._tray_icon:
            try: self._tray_icon.stop()
            except: pass
            self._tray_icon = None
        self._main()
        if saved_tab:
            st = saved_tab
            try: self.after(200, lambda: self._tabs_ref.set(st))
            except: pass
        if HAS_TRAY: self.after(600, self._init_tray)

    def _toggle_theme(self):
        new="light" if _theme=="dark" else "dark"
        def fo(a=1.0):
            a=max(a-0.15,0.0)
            try: self.attributes("-alpha",a)
            except: pass
            if a>0.0: self.after(12,lambda: fo(a))
            else:
                saved_tab = None
                try: saved_tab = self._tabs_ref.get()
                except: pass
                if hasattr(self,"_tray_icon") and self._tray_icon:
                    try: self._tray_icon.stop()
                    except: pass
                    self._tray_icon = None
                apply_theme(new); save_config({"theme":new})
                self._main()
                if saved_tab:
                    st = saved_tab
                    try: self.after(200, lambda: self._tabs_ref.set(st))
                    except: pass
                if HAS_TRAY: self.after(600, self._init_tray)
                fi(0.0)
        def fi(a=0.0):
            a=min(a+0.15,1.0)
            try: self.attributes("-alpha",a)
            except: pass
            if a<1.0: self.after(12,lambda: fi(a))
        fo()

    def _open_lang(self):
        if self._dropdown_visible:
            self._hide_dropdown()
        else:
            self._show_dropdown()

    def _show_dropdown(self):
        self._dropdown_visible = True
        self._dropdown.lift()
        self._dropdown.place(in_=self, relx=1.0, rely=0.0,
                             x=-self._dropdown.winfo_reqwidth()-22,
                             y=self._hdr_height + 4)
        self._dropdown_bind_id = self.bind_all("<Button-1>", self._dropdown_click_outside, add="+")

    def _hide_dropdown(self):
        self._dropdown_visible = False
        self._dropdown.place_forget()
        try:
            bid = getattr(self, "_dropdown_bind_id", None)
            if bid: self.unbind("<Button-1>", bid)
            else: self.unbind_all("<Button-1>")
        except: pass

    def _dropdown_click_outside(self, event):
        widget = event.widget
        w = widget
        while w is not None:
            if w is self._dropdown: return
            try: w = w.master
            except: break
        self._hide_dropdown()

    def _set_lang(self, code):
        self._set_lang_direct(code)

    def _on_tab_change(self):
        try:
            name = self._tabs_ref.get()
            if name == t("history_tab") and hasattr(self, "_ht") and self._ht:
                self._ht.refresh()
        except: pass


    def _init_tray(self):
        if not HAS_TRAY: return
        if self._tray_icon is not None: return 
        try:
            import os as _os
            ico_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo.ico")
            if _os.path.isfile(ico_path):
                img = Image.open(ico_path).resize((64,64))
            else:
                img = make_tray_icon()
            menu = pystray.Menu(
                pystray.MenuItem(t("tray_open"), self._tray_restore, default=True),
                pystray.MenuItem(t("tray_quit"), self._tray_quit))
            self._tray_icon = pystray.Icon("MTO", img, "MTO — Mp3ToOgg", menu)
            threading.Thread(target=self._tray_icon.run, daemon=True).start()
            self.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception: pass

    def _on_close(self):
        if HAS_TRAY and self._tray_icon:
            self.withdraw()
        else:
            self._quit_app()

    def _quit_app(self):
        log.info("App shutting down")
        if hasattr(self, "_tray_icon") and self._tray_icon:
            try:
                self._tray_icon.stop()
                self._tray_icon = None
            except: pass
        try: self.destroy()
        except: pass
        import time as _t
        _t.sleep(0.3)
        import sys; sys.exit(0)

    def _tray_restore(self, icon=None, item=None):
        self.after(0, self.deiconify)
        self.after(0, self.lift)

    def _tray_quit(self, icon=None, item=None):
        self.after(0, self._quit_app)


    def _check_update(self):
        ver, url, changelog = check_for_update()
        if ver and url:
            self.after(0, self._show_update_banner, ver, url, changelog)

    def _show_update_banner(self, ver, url, changelog=""):
        try:
            self._update_bar_lbl.configure(text=t("update_avail", ver=ver))
            self._update_bar_btn.configure(
                text=t("update_btn"),
                command=lambda: self._show_changelog(ver, url, changelog))
            self._update_bar.place(relx=1.0, rely=0.0, anchor="ne", x=-16, y=70)
            self._update_bar.lift()
        except: pass

    def _show_changelog(self, ver, url, changelog):
        """Show changelog as overlay inside main window with markdown bold support."""
        overlay = ctk.CTkFrame(self, fg_color=TH("bg"), corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        crd = ctk.CTkFrame(overlay, fg_color=TH("surface"), corner_radius=14,
                            border_width=1, border_color=TH("accent"), width=520)
        crd.place(relx=0.5, rely=0.5, anchor="center")

        hdr = ctk.CTkFrame(crd, fg_color=TH("surface2"), corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=f"🔔  MTO v{ver} — {t('whats_new')}",
            font=("Segoe UI",15,"bold"), text_color=TH("accent")).pack(
            side="left", padx=20, pady=12)
        ctk.CTkButton(hdr, text="✕", width=32, height=32,
            fg_color="transparent", hover_color=TH("error"),
            text_color=TH("subtext"), font=("Segoe UI",13,"bold"),
            command=overlay.destroy).pack(side="right", padx=8, pady=8)

        log_outer = ctk.CTkFrame(crd, fg_color="transparent")
        log_outer.pack(fill="both", expand=True, padx=16, pady=(12,8))

        import tkinter.font as tkfont
        normal_font = tkfont.Font(family="Segoe UI", size=11)
        bold_font   = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        log_txt = tk.Text(log_outer, font=normal_font, bg=TH("surface"),
            fg=TH("text"), wrap="word", relief="flat", bd=0,
            highlightthickness=0, height=14, width=55,
            selectbackground=TH("accent"), insertbackground=TH("text"))
        log_txt.pack(fill="both", expand=True)
        log_txt.tag_configure("bold", font=bold_font, foreground=TH("text"))
        log_txt.tag_configure("h2", font=tkfont.Font(family="Segoe UI",size=12,weight="bold"),
                               foreground=TH("accent"))

        import re as _re
        text = changelog if changelog else "No release notes available."
        for line in text.splitlines():
            line = line.rstrip()
            if line.startswith("## "):
                log_txt.insert("end", line[3:] + "\n", "h2")
            elif line.startswith("**") and line.endswith("**"):
                log_txt.insert("end", line[2:-2] + "\n", "bold")
            else:
                parts = _re.split(r'(\*\*[^*]+\*\*)', line)
                for part in parts:
                    if part.startswith("**") and part.endswith("**"):
                        log_txt.insert("end", part[2:-2], "bold")
                    else:
                        log_txt.insert("end", part)
                log_txt.insert("end", "\n")
        log_txt.configure(state="disabled")

        btn_row = ctk.CTkFrame(crd, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0,16))
        ctk.CTkButton(btn_row, text=t("update_later"), width=130, height=40,
            font=("Segoe UI",12), fg_color=TH("surface2"), hover_color=TH("surface3"),
            text_color=TH("subtext"), border_width=1, border_color=TH("border"),
            corner_radius=10, command=overlay.destroy).pack(side="left")
        AnimBtn(btn_row, text=t("update_btn"), width=200, height=40,
            variant="accent", font=("Segoe UI",12,"bold"),
            command=lambda: [overlay.destroy(),
                threading.Thread(target=self._do_update, args=(url,), daemon=True).start()]
        ).pack(side="right")

    def _do_update(self, url):
        log.info(f"Downloading update from: {url}")
        self.after(0, lambda: self._update_bar_lbl.configure(text="Ladataan päivitystä..."))
        self.after(0, lambda: self._update_bar_btn.configure(state="disabled"))
        bat = download_update(url)
        if bat:
            self.after(0, lambda: self._update_bar_lbl.configure(
                text="Valmis! Käynnistetään päivitys..."))
            self.after(800, lambda: self._apply_update(bat))
        else:
            self.after(0, lambda: self._update_bar_lbl.configure(
                text="⚠  Lataus epäonnistui"))
            self.after(0, lambda: self._update_bar_btn.configure(state="normal"))

    def _apply_update(self, bat):
        subprocess.Popen(
            ["cmd", "/c", bat],
            cwd=os.path.dirname(bat),
            creationflags=NO_WINDOW
        )
        self._quit_app()


    def _open_accent_picker(self):
        if hasattr(self,"_accent_popup") and self._accent_popup:
            try: self._accent_popup.destroy()
            except: pass
        popup = ctk.CTkFrame(self, fg_color=TH("surface"), corner_radius=12,
                              border_width=1, border_color=TH("border_hi"))
        self._accent_popup = popup

        inner = ctk.CTkFrame(popup, fg_color="transparent")
        inner.pack(padx=10, pady=10)
        ctk.CTkLabel(inner, text=t("accent_label"),
            font=("Segoe UI",10,"bold"), text_color=TH("subtext")).pack(anchor="w", pady=(0,6))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack()
        for hex_color, name in ACCENT_PRESETS:
            swatch = ctk.CTkButton(row, text="", width=32, height=32,
                fg_color=hex_color, hover_color=hex_color,
                corner_radius=16, border_width=2,
                border_color=TH("border") if hex_color != TH("accent") else TH("text"),
                command=lambda h=hex_color: self._set_accent(h))
            swatch.pack(side="left", padx=3, pady=2)

        popup.update_idletasks()
        bx = self._accent_btn.winfo_rootx()
        by = self._accent_btn.winfo_rooty() + self._accent_btn.winfo_height() + 4
        popup.place(in_=self, x=bx - self.winfo_rootx(),
                    y=by - self.winfo_rooty())
        popup.lift()
        self._accent_bind_id = self.bind_all("<Button-1>", self._accent_outside, add="+")

    def _accent_outside(self, event):
        if not hasattr(self,"_accent_popup") or not self._accent_popup: return
        w = event.widget
        while w is not None:
            if w is self._accent_popup: return
            try: w = w.master
            except: break
        self._close_accent()

    def _close_accent(self):
        try:
            bid = getattr(self, "_accent_bind_id", None)
            if bid: self.unbind("<Button-1>", bid)
            else: self.unbind_all("<Button-1>")
            if hasattr(self,"_accent_popup") and self._accent_popup:
                self._accent_popup.destroy()
                self._accent_popup = None
        except: pass


class TutorialOverlay:
    """First-run tutorial overlay that highlights UI elements with an info card."""

    STEPS = ["tut1","tut2","tut3","tut4"]

    def __init__(self, root, get_widget_cb, on_done):
        self._root       = root
        self._get_widget = get_widget_cb
        self._on_done    = on_done
        self._step       = 0
        self._phase      = 1
        self._steps      = self.STEPS

        surf = TH("surface"); acc = TH("accent")
        txt  = TH("text");    sub = TH("subtext")
        s2   = TH("surface2"); bdr = TH("border"); bg = TH("bg")

        self._card = ctk.CTkFrame(root, fg_color=surf, corner_radius=14,
            border_width=2, border_color=acc, width=300)

        self._title_lbl = ctk.CTkLabel(self._card, text="",
            font=("Segoe UI",13,"bold"), text_color=acc,
            wraplength=260, justify="left", anchor="w")
        self._title_lbl.pack(padx=16, pady=(12,0), fill="x")

        ctk.CTkFrame(self._card, fg_color=bdr, height=1,
            corner_radius=0).pack(fill="x", padx=12, pady=8)

        self._body_lbl = ctk.CTkLabel(self._card, text="",
            font=("Segoe UI",11), text_color=txt,
            wraplength=260, justify="left", anchor="w")
        self._body_lbl.pack(padx=16, pady=(0,6), fill="x")

        self._step_lbl = ctk.CTkLabel(self._card, text="",
            font=("Segoe UI",9), text_color=sub, anchor="w")
        self._step_lbl.pack(padx=16, pady=(0,4), fill="x")

        ctk.CTkFrame(self._card, fg_color=bdr, height=1,
            corner_radius=0).pack(fill="x", padx=12, pady=(0,8))

        br = ctk.CTkFrame(self._card, fg_color="transparent")
        br.pack(fill="x", padx=12, pady=(0,14))

        self._skip_btn = ctk.CTkButton(br, text=t("tut_skip"),
            width=90, height=34, font=("Segoe UI",10),
            fg_color=s2, hover_color=bdr, text_color=sub,
            border_width=1, border_color=bdr, corner_radius=8,
            command=self._skip)
        self._skip_btn.pack(side="left")

        self._next_btn = AnimBtn(br, text=t("tut_next"),
            width=150, height=34, variant="accent",
            font=("Segoe UI",11,"bold"), command=self._next)
        self._next_btn.pack(side="right")

        self._bind_id = self._root.bind("<Configure>", self._on_resize, add="+")
        self._root.after(100, self._show_step)

    def _show_step(self):
        sid = self._steps[self._step]
        self._title_lbl.configure(text="▲  " + t(f"{sid}_title"))
        self._body_lbl.configure(text=t(f"{sid}_body"))
        self._step_lbl.configure(text=f"{self._step+1} / {len(self._steps)}")
        is_last = self._step == len(self._steps)-1
        if is_last: self._next_btn.configure(text=t("tut_finish"))
        else:       self._next_btn.configure(text=t("tut_next"))
        self._root.update_idletasks()
        self._place_card(sid)
        self._card.lift()

    def _place_card(self, sid):
        self._root.update_idletasks()
        rw = self._root.winfo_width()
        rh = self._root.winfo_height()
        cw = max(self._card.winfo_reqwidth(), 280)
        ch = max(self._card.winfo_reqheight(), 160)
        widget = self._get_widget(sid)
        if widget:
            try:
                rx = self._root.winfo_rootx()
                ry = self._root.winfo_rooty()
                wx = widget.winfo_rootx() - rx
                wy = widget.winfo_rooty() - ry
                wh = widget.winfo_height()
                cy = wy + wh + 10
                cx = wx
                if cy + ch > rh - 10:
                    cy = wy - ch - 10
                if cy < 10:
                    cy = max(10, rh // 2 - ch // 2)
                cx = max(10, min(cx, rw - cw - 10))
                cy = max(10, min(cy, rh - ch - 10))
                self._card.place(x=cx, y=cy)
                return
            except: pass
        self._card.place(
            x=max(10, rw//2 - cw//2),
            y=max(10, rh//2 - ch//2))

    def _next(self):
        if self._step < len(self._steps)-1:
            self._step += 1; self._show_step()
        else:
            self._finish()


    def _on_resize(self, event=None):
        if hasattr(self, "_steps") and self._step < len(self._steps):
            try:
                sid = self._steps[self._step]
                self._root.update_idletasks()
                self._place_card(sid)
                self._card.lift()
            except: pass

    def _skip(self): self._finish()

    def _finish(self):
        try: self._root.unbind("<Configure>", self._bind_id)
        except: pass
        try: self._card.destroy()
        except: pass
        self._on_done()

if __name__=="__main__":
    app=App(); app.mainloop()

# -*- coding: utf-8 -*-

# MTO — Mp3ToOgg
# Copyright © 2026 @MorkulaArttu. All rights reserved.
# Licensed under GNU GPL v3 — see LICENSE for details
# https://github.com/morkulaarttu/MTO
#
# MTO is a free Windows tool for My Winter Car players.
# It converts MP3 files to OGG format and downloads YouTube audio
# directly into the game's Radio folder.