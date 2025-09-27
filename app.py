import streamlit as st
import image_to_list
import re
import pandas as pd
import streamlit as st
from streamlit_cropper import st_cropper
from PIL import Image
import io

st.set_page_config(page_title="Bill Spliter", page_icon="💵")

if "tip" not in st.session_state:
    st.session_state.tip = None
if "show_tip_input" not in st.session_state:
    st.session_state.show_tip_input = False
if "splitters" not in st.session_state:
    st.session_state.splitters = []
if "pending_remove" not in st.session_state:
    st.session_state.pending_remove = None
# אתחול חובה (לפני add/remove/show)
if "splitters" not in st.session_state:
    st.session_state.splitters = []
if "pending_remove" not in st.session_state:
    st.session_state.pending_remove = None


st.markdown(
    """
    <style>
    body, .stApp , p{
        direction: rtl;
        text-align: right;
    }
    /* טבלה RTL */
    thead tr th:first-child {text-align: right !important;}
    tbody td {text-align: right !important;}
    [data-testid="stTable"] {direction: rtl}

    /* רשימות RTL */
    ul {
        direction: rtl;
        text-align: right;
        list-style-position: inside;
    }

    html[lang="he"] body, .stApp { direction: rtl; text-align: right; }
    .pills-wrap {
    display: flex; flex-wrap: wrap; gap: 0.3rem;
    padding: .5rem; border:1px solid rgba(148,163,184,.25);
    border-radius: .75rem; min-height: 40px; background: #e0ecfa;
    }
    .name-pill {
    display: inline-flex; align-items: center; gap: .3rem;
    padding: .18rem .45rem; border-radius: 999px;
    background: linear-gradient(90deg, rgba(126,34,206,.15), rgba(245,158,11,.15));
    color: #24126a; font-size: 0.95rem; font-family: inherit; margin: 0;
    border: 2px solid #7e22ce; box-shadow: 0 2px 8px 0 rgba(126,34,206,.08);
    transition: box-shadow 0.2s;
    }
    .name-pill:hover { box-shadow: 0 4px 16px 0 rgba(126,34,206,.18); border-color: #f59e0b; }

        /* עיצוב ברירת מחדל לכפתורי טיפ */
    .stButton > button{
    background:#f4f7ff; color:#24126a;
    border:1.5px solid rgba(148,163,184,.35);
    border-radius:999px; padding:.45rem .9rem;
    font-weight:600; cursor:pointer;
    box-shadow:0 2px 8px rgba(126,34,206,.08);
    transition:.15s all ease;
    }
    .stButton > button:hover{
    box-shadow:0 4px 16px rgba(126,34,206,.18);
    border-color:#7e22ce;
    }
    /* כפתור נבחר (tip-selected) */
    .stButton > button.tip-selected {
    background:linear-gradient(90deg, rgba(126,34,206,.25), rgba(245,158,11,.25));
    border-color:#7e22ce; color:#111827;
    }
    .hint { color:#94a3b8; font-size:.9rem; }

    </style>
    """,
    unsafe_allow_html=True
)

def create_menu(items):
    # הזנת הסועדים
    if not st.session_state["items"]:
        st.subheader("לא נמצאו פריטים בתמונה")
        return    
    st.warning("""
    הפריטים בתמונה מזוהים באמצעות בינה מלאכותית, ולכן ייתכנו אי-דיוקים בזיהוי או במחירים.  
    מומלץ לעבור על הנתונים ולוודא שהם תואמים לחשבונית שצולמה.  
    במידת הצורך, ניתן להעלות תמונה חדשה ולבצע ניתוח חוזר.
    """)

        # פונקציות עזר
    def add_name(name: str):
        name = (name or "").strip()
        if not name:
            st.toast("חסר תפקיד להזנה", icon="⚠️"); return
        if name in st.session_state.splitters:
            st.toast("התפקיד כבר קיים ברשימה", icon="ℹ️"); return
        st.session_state.splitters.append(name)
        st.toast(f"נוסף: {name}", icon="✅")

    def remove_name(name: str):
        if name in st.session_state.splitters:
            st.session_state.splitters.remove(name)
            st.toast(f"הוסר: {name}", icon="🗑️")

    # ---------- טופס הוספה ----------
    with st.form("add_name_form", clear_on_submit=True):
        new_name = st.text_input("הכנס את שמות הסועדים", key="name_input")
        submitted = st.form_submit_button("➕ הוסף")
        if submitted:
            add_name(new_name)

    st.write("")  # רווח קטן

    # ---------- תצוגת תגיות + מחיקה ----------
    st.subheader("שמות הסועדים")

    splitters = st.session_state.splitters

    if not st.session_state.splitters:
        st.markdown('<div class="hint">אין תגיות עדיין. הוסף סועד ראשון.</div>', unsafe_allow_html=True)
    else:
        PER_ROW = 6  # כמה pills בשורה (אפשר לשנות ל-4/5/7)
        splitters = st.session_state.splitters

        # פריסה לשורות
        for start in range(0, len(splitters), PER_ROW):
            row = splitters[start:start+PER_ROW]
            cols = st.columns(len(row))
            for i, name in enumerate(row):
                with cols[i]:
                    # הכפתור נראה כמו "גלולה" בזכות ה-CSS הכללי שלך לכפתורים
                    if st.button(f"{name} ✕", key=f"pill_{name}", help="לחץ להסרה"):
                        st.session_state.pending_remove = name

    # תיבת אישור להסרה (נשארת כמו שיש לך)
    if st.session_state.pending_remove:
        st.warning(f"האם להסיר את '{st.session_state.pending_remove}' מהרשימה?")
        col_ok, col_cancel = st.columns([1, 1])
        with col_ok:
            if st.button("אישור", key="confirm_remove"):
                remove_name(st.session_state.pending_remove)
                st.session_state.pending_remove = None
                st.rerun()
        with col_cancel:
            if st.button("ביטול", key="cancel_remove"):
                st.session_state.pending_remove = None


    # רשימת הפריטים

    st.subheader("פריטים", divider=True)
    total_price = sum(float(i["price_per_unit"]) * int(i["quantity"]) for i in items)
    for index, item in enumerate(items):
        for i in range(int(item["quantity"])):
            col1, col2 = st.columns([0.4, 0.6])
            with col1:
                st.text(f"{item['name']} - ₪{item['price_per_unit']}")
            with col2:
                st.multiselect("בחר סועדים",
                    options= splitters,
                    key=f"{index}_{i}",
                    label_visibility="collapsed",
                    placeholder="כולם"
                )
          



    # ---------- TIP ----------
    st.subheader("טיפ")
    cols = st.columns(5)

    # כפתור עזר – יוצר class שונה אם נבחר
    def tip_button(label, value, col):
        with col:
            btn_ph = st.empty()
            css_class = "tip-selected" if st.session_state.tip == value else ""
            if btn_ph.button(label, key=f"tip_{value}"):
                st.session_state.tip = value
                st.rerun()
            # הזרקת class לכפתור (עם JS קטן)
            st.markdown(f"""
            <script>
            var btns = window.parent.document.querySelectorAll('button[kind="secondary"][data-testid="baseButton-tip_{value}"]');
            if(btns.length) {{
                btns[0].classList.add("{css_class}");
            }}
            </script>
            """, unsafe_allow_html=True)

    tip_button("0", 0, cols[0])
    tip_button("10", 10, cols[1])
    tip_button("12", 12, cols[2])
    tip_button("15", 15, cols[3])

    with cols[4]:
        slot = st.empty()
        if not st.session_state.show_tip_input:
            with slot:
                if st.button("הזן ידנית", key="open_tip_btn"):
                    st.session_state.show_tip_input = True
                    st.rerun()
            if isinstance(st.session_state.tip, (int, float)) and st.session_state.tip not in (0, 10, 12, 15):
                # גם לטיפ ידני נוסיף class
                st.markdown("""
                <script>
                var btns = window.parent.document.querySelectorAll('button[kind="secondary"][data-testid="baseButton-open_tip_btn"]');
                if(btns.length){ btns[0].classList.add("tip-selected"); }
                </script>
                """, unsafe_allow_html=True)
        else:
            with slot.form("manual_tip_form", clear_on_submit=True):
                new_tip = st.text_input("כמה טיפ?", key="tip_input", placeholder="למשל: 20")
                submitted = st.form_submit_button("שלח")
            if submitted:
                val = new_tip.strip()
                if val:
                    try:
                        val_num = float(val.replace(",", "."))
                        st.session_state.tip = int(val_num) if val_num.is_integer() else val_num
                        st.session_state.show_tip_input = False
                        st.rerun()
                    except ValueError:
                        st.error("אנא הזן מספר תקין")
                else:
                    st.error("נא להכניס ערך")

        # הצגה
    if st.session_state.tip is not None:
        st.markdown(f"**הטיפ שנבחר:** % {st.session_state.tip} ")
    else:
        st.markdown("_לא נבחר טיפ עדיין_")

    tip_percent = st.session_state.tip
    tip_amount = total_price * ((tip_percent or 0) / 100)
    final_price = total_price + tip_amount

    # נתונים
    st.divider()
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        st.metric("סכום ללא טיפ" ,f"{total_price} ש\"ח")
    with col2:
        st.metric("סכום כולל טיפ" ,f"{round(final_price,2)} ש\"ח")

    # כפתור חישוב
    calculate_btn = st.button("חשב מחיר לכל סועד", disabled=not splitters)

    if calculate_btn:
        results = split_bill(tip_percent, items)
        st.subheader(" טבלת פירוט לכל סועד")
        table_data = []
        for person, data in results.items():
            table_data.append({
                "סועד": person,
                "פריטים": "\n".join(f"- {it}" for it in data["items"]), ###
                "מספר פריטים": data['item_count'],
                "מחיר": f"₪{data['price']:.2f}",
                "מחיר כולל טיפ": f"₪{data['price_with_tip']:.2f}"
            })
        df = pd.DataFrame(table_data)
        df.set_index("סועד", inplace=True)
        st.table(df)


def split_item(item_spliters,dinners_dict,item,tip_percent):
    for person in item_spliters:
        if person not in dinners_dict:
            dinners_dict[person] = {
                "items":[], 
                "item_count": 0,
                "price": 0.0,
                "price_with_tip": 0.0
            }
        dinners_dict[person]["item_count"] += 1
        dinners_dict[person]["items"].append(item['name']) 
        share = item["price_per_unit"] / len(item_spliters)
        dinners_dict[person]["price"] += share
        tip_amount = dinners_dict[person]["price"] * (tip_percent / 100)
        dinners_dict[person]["price_with_tip"] = dinners_dict[person]["price"] + tip_amount

def split_bill(tip_percent,items):
    people = {}
    for index, item in enumerate(items):
        for i in range(int(item["quantity"])):
            item_spliters = st.session_state.get(f"{index}_{i}")
            if item_spliters:
                split_item(item_spliters,people,item,tip_percent)
            else:
                split_item(st.session_state["splitters"],people,item,tip_percent)
                
    return people


if "items" in st.session_state:      
    if st.button("🗑️ נקה והעלה מחדש", use_container_width=True):
        if "items" in st.session_state:
            del st.session_state["items"]
        if "upload_counter" not in st.session_state:
            st.session_state["upload_counter"] = 0
        st.session_state["upload_counter"] += 1
        st.rerun()
    create_menu(st.session_state["items"])

else:
    upload_key = f"image_uploader_{st.session_state.get('upload_counter', 0)}"
    img_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if img_file:
        
        img = Image.open(img_file)
        if img.format not in ["JPEG", "PNG"]:
            st.error("פורמט תמונה לא נתמך. נא להעלות קובץ PNG או JPG.")

        else:
            img = img.resize((800, int(800 * cropped_img.height / cropped_img.width)))
            if st.button("נתח את החשבונית"):
                with st.spinner("מנתח את החשבונית..."):
                    try:
                        buffer = io.BytesIO()
                        img.save(buffer, format="PNG")
                        buffer.seek(0)
                        st.session_state["items"] = image_to_list.get_menu_items(buffer)
                    except Exception:
                        st.session_state["items"] = []
                st.rerun()