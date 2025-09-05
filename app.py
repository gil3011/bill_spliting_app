import streamlit as st
import image_to_list
import re
import pandas as pd

st.set_page_config(page_title="Bill Spliter", page_icon="💵")

st.markdown(
    """
    <style>
    body, .stApp , p{
        direction: rtl;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def create_menu(items):
    # הזנת הסועדים
    try:
        st.warning("""
               ממולץ לעבור על הפריטים והנתונים ולוודא שהמחירים מתאימים לחשבונית שצולמה\n
                ניתן להעלות תמונה מחדש במקרה הצורך
               """)
        st.divider()
        col1, col2  = st.columns([0.4, 0.6])
        with col1:
            st.subheader("הזן שמות סועדים:")
        with col2: 
            st.text_input("a", key="dinners", label_visibility="collapsed")
        splitters = []
        update_btn = st.button("עדכן סועדים", use_container_width=True)
        if update_btn:
            splitters = [p.strip() for p in re.split(r'[,\s]+', st.session_state.get("dinners", "")) if p.strip()]
            st.session_state["splitters"] = splitters
        elif "splitters" in st.session_state:
            splitters = st.session_state["splitters"]

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

        # בחירת טיפ
        st.divider()
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.subheader("טיפ באחוזים:")
        with col2: 
            tip_percent = st.number_input("הכנס אחוז טיפ", min_value=0, value=0, step=1, label_visibility="collapsed")
            tip_amount = total_price * (tip_percent / 100)
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
                    "מספר פריטים": data['item_count'],
                    "מחיר": f"₪{data['price']:.2f}",
                    "מחיר כולל טיפ": f"₪{data['price_with_tip']:.2f}"
                })
            df = pd.DataFrame(table_data)
            df.set_index("סועד", inplace=True)
            # Display as a static table
            st.table(df)
    except Exception as e:
        st.subheader("קריאת התמונה נכשלה")

def split_item(item_spliters,dinners_dict,item,tip_percent):
    for person in item_spliters:
        if person not in dinners_dict:
            dinners_dict[person] = {
                "item_count": 0,
                "price": 0.0,
                "price_with_tip": 0.0
            }
        dinners_dict[person]["item_count"] += 1
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
        # Clear the items and reset uploader
        if "items" in st.session_state:
            del st.session_state["items"]
        # Clear the file uploader by incrementing a counter
        if "upload_counter" not in st.session_state:
            st.session_state["upload_counter"] = 0
        st.session_state["upload_counter"] += 1
        st.rerun()
    create_menu(st.session_state["items"])

else:
    upload_key = f"image_uploader_{st.session_state.get('upload_counter', 0)}"
    uploaded_file = st.file_uploader("בחר תמונה", type=["jpg", "jpeg", "png"], key=upload_key)
    if uploaded_file:
        with st.spinner("מנתח את החשבונית..."):
            st.session_state["items"] = image_to_list.get_menu_items(uploaded_file)
        st.rerun()