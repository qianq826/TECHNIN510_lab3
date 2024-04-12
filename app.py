import os
from dataclasses import dataclass
import datetime

import streamlit as st
import psycopg2
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Prompt:
    title: str
    prompt: str
    is_favorite: bool
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None

def setup_database():
    con = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()
    return con, cur

def prompt_form(prompt=None):
    default = Prompt("", "", False) if prompt is None else prompt
    with st.form(key="prompt_form", clear_on_submit=True):
        title = st.text_input("Title", value=default.title)
        prompt_content = st.text_area("Prompt", height=200, value=default.prompt)
        is_favorite = st.checkbox("Favorite", value=default.is_favorite)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if not title or not prompt_content:
                st.error('Please fill in both the title and prompt fields.')
                return
            return Prompt(title, prompt_content, is_favorite)

def display_prompts(cur):
    cur.execute("SELECT * FROM prompts ORDER BY created_at DESC")  # Default sort by created date 
    prompts = cur.fetchall()
    # TODO: Add a search bar
    search_query = st.text_input("Search")
    # TODO: Add a sort by date
    sort_order = st.radio("Sort by", options = ["Created date", "Title"])
    sort_order_sql = "created_at DESC" if sort_order == "Created Date" else "title ASC"
    
    sql = f"SELECT * FROM prompts WHERE title LIKE %s ORDER BY {sort_order_sql}"
    cur.execute(sql, ('%' + search_query + '%',))
    prompts = cur.fetchall()


    for p in prompts:
        with st.expander(f"{p[1]} (created on {p[5]})"):
            st.code(p[2])
            # TODO: Add a edit function
            if st.button("Edit", key=f"edit-{p[0]}"):
                edit_prompt(p,cur,con)
            if st.button("Delete", key=f"del-{p[0]}"):
                cur.execute("DELETE FROM prompts WHERE id = %s", (p[0],))
                con.commit()
                st.rerun()
            # TODO: Add favorite button
            if st.button("Favorite", key=f"fav-{p[0]}"):
                cur.execute("UPDATE prompts SET is_favorite = NOT is_favorite WHERE id = %s", (p[0],))
                con.commit()
                st.experimental_rerun()

def edit_prompt(prompt, cur, con):
    edited_prompt = prompt_form(prompt=Prompt(prompt[1], prompt[2], prompt[3]))
    if edited_prompt:
        cur.execute("UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s WHERE id = %s",
                    (edited_prompt.title, edited_prompt.prompt, edited_prompt.is_favorite, prompt[0]))
        con.commit()
        st.success("Prompt updated successfully!")
        st.experimental_rerun()

if __name__ == "__main__":
    st.title("Promptbase")
    st.subheader("A simple app to store and retrieve prompts")

    con, cur = setup_database()

    new_prompt = prompt_form()
    if new_prompt:
        try: 
            cur.execute(
                "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s)",
                (new_prompt.title, new_prompt.prompt, new_prompt.is_favorite)
            )
            con.commit()
            st.success("Prompt added successfully!")
        except psycopg2.Error as e:
            st.error(f"Database error: {e}")

    display_prompts(cur)
    con.close()