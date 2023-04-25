import os
import openai
import replicate
import streamlit as st

# Set your API tokens
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.title("SongwritingGPT")
st.write("This application leverages the power of GPT-4 to create music based on your chosen genre, time signature, and measure length. Please note that, as a beta version, the generated melodies may not always be accurate on the first attempt, but the app will automatically regenerate them if needed. For any questions or feedback, feel free to reach out to me at ethanjags@berkeley.edu.")

# Select a genre
genre_options = ["Jazz", "Rock", "Pop", "Type your own genre..."]
genre = st.selectbox("Select a genre (or input your own):", genre_options)

if genre == "Type your own genre...":
    genre = st.text_input("Type a custom genre:")

# Select time signature and measure length
time_signature = st.number_input("Select time signature:", min_value=1, max_value=8, value=4, step=1)
measure_length = st.number_input("Enter measure length:", min_value=1, max_value=16, value=4, step=1)
tempo = st.slider("Enter tempo (beats per minute):", min_value=30, max_value=300, value=120, step=1)
# sample_width = st.number_input("Enter sample width:", min_value=1, max_value=100, value=10, step=1)
# seed = st.number_input("Enter random seed (-1 for random):", min_value=-1, max_value=10000, value=-1, step=1)


# Generate notes and chords using GPT-4 based on the selected genre, time signature, and measure length
openai.api_key = OPENAI_API_KEY
error = False
prevResult = False

def generate_notes_chords(genre, time_signature, measure_length, error, prevResult):
    
    
    num_attempts = 0
    itWorked = False
    while not itWorked and num_attempts < 5:
        prompt = f"Generate a simple melody and chord progression inspired by john mayer in tinynotation format for a {genre.lower()} song with {time_signature}/4 time signature and {measure_length} measures. Ensure that both the melody and chords have the same number of measures and each measure contains the same amount of beats. The generated output should contain exactly two lines: the first line for the melody notes and the second line for the chords. Ensure there is only one chord per measure. Separate melody notes with '|' and chords with '|'. Make sure the output contains no extra words or punctuation.     The music must contain a variety of note lengths. A 4 after a note indicates a quarter note, an 8 means an eighth note, a 2 means a half note. It should be interesting, involve different lengths of notes and melodic intervals. It should be based on music theory and sound good.     Here is an example: D4 A4 B4 F#4 | G8 A8 G8 A8 G4 A4 | B4 F#4 G4 D4 | G8 A8 G8 A8 G4 A4 | B4 F#4 G4 D4 | G8 A8 G8 A8 G4 A4 | B4 F#4 G2 \n D | A | Bm | F#m | G | D | A"
    
        if error and prevResult:
            prompt += f"\n{prevResult} did not work. Please fix the error. This is the error that was returned: {error}"

        message = [{"role": "user", "content": prompt}]
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=message,
                max_tokens=100,
                n=1,
                stop=None,
                temperature=0.7,
            )

            result = response['choices'][0]['message']['content'].strip()
            split_result = result.split("\n")
            if len(split_result) != 2:
                st.write(result)
                st.error("Generated output is not in the expected format. Please try again.")
                error = "Not in expected format"
                prevResult = result
            else:
                itWorked = True
                return result
        except Exception as e:
            st.error(f"Error: {e}. Retrying...")
            error = e
            num_attempts += 1

    st.error("Failed to generate chords and melody after 5 GPT attempts. Please try again.")
    return None

if st.button("Generate Chords and Melody"):
    result = generate_notes_chords(genre, time_signature, measure_length, error, prevResult)
    
    if result:
        split_result = result.split("\n")
        if len(split_result) != 2:
            st.write(result)
            st.error("Generated output is not in the expected format. Please try again.")
        else:
            notes, chords = split_result
            st.session_state.notes = notes
            st.session_state.chords = chords
        
            st.write(f"**Generated {genre} Notes:**")
            st.write(st.session_state.notes)

            st.write(f"**Generated {genre} Chords:**")
            st.write(st.session_state.chords)


if st.button("Generate mp3 file and sheet music"):
    firstTime = True
    result = None  # Initialize the result variable
    if "notes" not in st.session_state or "chords" not in st.session_state:
        firstTime = False
    num_attempts = 0
    while num_attempts < 5:
        try:
            if not firstTime:
                thisWorked = False
                while not thisWorked and num_attempts < 5:
                    if not firstTime:
                        prevResult = result
                    result = generate_notes_chords(genre, time_signature, measure_length, error, prevResult)
                    if result:
                        split_result = result.split("\n")
                        if len(split_result) != 2:
                            st.write(result)
                            st.error("Generated output is not in the expected format. Please try again.")
                            num_attempts += 1
                        else:
                            thisWorked = True
                            notes, chords = split_result
                            st.session_state.notes = notes
                            st.session_state.chords = chords
                            st.write(notes)
                            st.write(chords)

            # Use st.session_state.notes and st.session_state.chords instead of result
            input_data = {
                "notes": st.session_state.notes,
                "chords": st.session_state.chords,
                "time_signature": time_signature,
                "tempo": tempo,
            }

            output = replicate.run(
                "andreasjansson/music-inpainting-bert:58bdc2073c9c07abcc4200fe808e15b1a555dbb1390e70f5daa6b3d81bd11fb1",
                input=input_data,
                api_token=REPLICATE_API_TOKEN,
            )
            st.write(f"**Generated {genre} Notes:**")
            st.write(st.session_state.notes)

            st.write(f"**Generated {genre} Chords:**")
            st.write(st.session_state.chords)
            
            st.write(f"**Generated Music:**")
            st.audio(output['mp3'])

            st.markdown(f"[Download MP3]({output['mp3']})")
            st.markdown(f"[Download MIDI]({output['midi']})")

            st.write(f"**Generated Score:**")
            st.image(output['score'], width=800)

            st.markdown(f"[Download Score]({output['score']})")
            break
        except Exception as e:
            st.error(f"Error: {e}. Retrying...")
            num_attempts += 1
            firstTime = False

    if num_attempts == 5:
        st.error("Failed to generate music after 5 GPT and/or Replicate attempts. Please try again.")

