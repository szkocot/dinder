import streamlit as st
import pandas as pd
from PIL import Image
from typing import List
import pydicom


# TODO: allow using keyboard for buttons

class Dinder():
    def __init__(self):
        if "target_height" not in st.session_state:
            st.session_state.target_height: int = 500
        if "counter" not in st.session_state:
            st.session_state.counter: int = 0
        if "uploaded_files" not in st.session_state:
            st.session_state.uploaded_files: List = []
        if "label" not in st.session_state:
            st.session_state.label: str = ""
        if "results" not in st.session_state:
            st.session_state.results: dict = {}
        if "image" not in st.session_state:
            st.session_state.image: Image = None

    def run(self) -> None:
        """
        Entry point of the app. Calls other methods to show the sidebar, select images, create a task, and proceed to labeling.
        """
        st.set_page_config(
            page_title="Dinder",
            page_icon="🪔",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        self.show_sidebar()

        if self.should_proceed():
            self.label_images()

    def show_sidebar(self) -> None:
        """
        Shows the sidebar with options to select images, create a task, and proceed to labeling.
        """
        st.sidebar.title("Dinder")
        st.sidebar.header(
            "Welcome to Dinder! Tinder for quick image labeling.")

        self.select_images()
        self.create_task()
        self.proceed_to_labeling()
        st.slider("Adjust image height", min_value=0, max_value=2000,
                  step=100, key="target_height", on_change=self.display_image)

    def select_images(self) -> None:
        """
        Allows the user to select images to label.
        """
        st.sidebar.subheader("Select images to label")
        st.session_state.uploaded_files = st.sidebar.file_uploader(
            "Upload images to label", accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "dicom", "dcm"])

    def reset_results(self) -> None:
        """
        Resets the results when new images are uploaded.
        """
        st.session_state.results = {
            file.name: -1 for file in st.session_state.uploaded_files}

    def create_task(self) -> None:
        """
        Allows the user to create a task by entering a label.
        """
        st.sidebar.subheader("Create a task")
        st.session_state.label = st.sidebar.text_input(
            "Enter a label for the task")

    def proceed_to_labeling(self) -> None:
        """
        Allows the user to proceed to labeling by clicking a button.
        """
        st.sidebar.subheader("Proceed to labeling")
        st.sidebar.write("Click the button below to proceed to labeling.")
        self.proceed = st.sidebar.button(
            "Proceed to labeling", on_click=self.reset_results)

    def should_proceed(self) -> bool:
        """
        Checks if the user has entered the necessary information before proceeding to labeling.
        """
        if not self.proceed:
            return False

        if len(st.session_state.uploaded_files) == 0:
            st.error("Please upload images to label.")
            return False

        if st.session_state.label == "":
            st.error("Please enter a label for the task.")
            return False

        return True

    def label_images(self) -> None:
        """
        Displays the images and buttons for labeling.
        """
        # empty placeholders
        self.img_placeholder = st.empty()
        self.buttons_placeholder = st.empty()

        self.display_image()

    def display_image(self) -> None:
        """
        Displays the current image and buttons for labeling.
        """
        uploaded_file = st.session_state.uploaded_files[st.session_state.counter]
        image = self.read_image(uploaded_file)
        st.session_state.image = image
        width, height = image.size
        new_width = int(width * st.session_state.target_height / height)
        image = image.resize((new_width, st.session_state.target_height))
        title = f"{st.session_state.counter + 1}/{len(st.session_state.uploaded_files)}: {uploaded_file.name}"
        if st.session_state.results[uploaded_file.name] == 1:
            title += " is ✅"
        elif st.session_state.results[uploaded_file.name] == 0:
            title += " is ❌"
        st.title(title)
        st.image(image)
        self.clean_image()

        columns = st.columns(4)
        with columns[0]:
            st.button(
                "❌", key=f'no_{st.session_state.counter}', on_click=self.save_results_no)
        with columns[1]:
            st.button(
                "⏮️", key=f'back_{st.session_state.counter}', on_click=self.decrease_counter)
        with columns[2]:
            st.button(
                "⏭️", key=f'skip_{st.session_state.counter}', on_click=self.increase_counter)
        with columns[3]:
            st.button(
                "✅", key=f'yes_{st.session_state.counter}', on_click=self.save_results_yes)

    def clean_image(self) -> None:
        """
        Closes the image to free up memory.
        """
        if st.session_state.image is not None:
            st.session_state.image.close()

    def read_image(self, uploaded_file):
        if uploaded_file.name.endswith(".dcm") or uploaded_file.name.endswith(".dicom"):
            with pydicom.dcmread(uploaded_file) as dicom_image:
                image = dicom_image.pixel_array
                # normalize the image to 0-255
                image = (image / image.max()) * 255
                image = image.astype("uint8")
                image = Image.fromarray(image)
        else:
            image = Image.open(uploaded_file).convert("RGB")
        return image

    def increase_counter(self) -> None:
        """
        Increases the counter to move to the next image and displays it.
        """
        st.session_state.counter += 1
        if st.session_state.counter < len(st.session_state.uploaded_files):
            self.display_image()
        else:
            st.write("You finished labeling!")
            st.balloons()
            # download results as csv
            st.write("Click the button below to download the results.")
            self.download_results()
            st.session_state.counter = 0

    def decrease_counter(self) -> None:
        """
        Decreases the counter to move to the previous image and displays it.
        """
        if st.session_state.counter > 0:
            st.session_state.counter -= 1
        self.display_image()

    def save_results_yes(self) -> None:
        """
        Saves the result of the current image as 1 (yes) and moves to the next image.
        """
        st.session_state.results[st.session_state.uploaded_files[st.session_state.counter].name] = 1
        self.increase_counter()

    def save_results_no(self) -> None:
        """
        Saves the result of the current image as 0 (no) and moves to the next image.
        """
        st.session_state.results[st.session_state.uploaded_files[st.session_state.counter].name] = 0
        self.increase_counter()

    def download_results(self) -> None:
        """
        Downloads the results as a CSV file.
        """
        # convert dictionary to dataframe
        results_df = pd.DataFrame.from_dict(
            st.session_state.results, orient="index")
        results_df.columns = [st.session_state.label]

        # download dataframe as csv
        csv = results_df.to_csv().encode('utf-8')
        st.download_button('Download CSV', data=csv,
                           file_name=f"{st.session_state.label}.csv", mime='text/csv')


if __name__ == "__main__":
    dinder = Dinder()
    dinder.run()
