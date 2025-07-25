import { createSlice,createAsyncThunk } from "@reduxjs/toolkit";
import axios from '../utils/auth'
import toast from "react-hot-toast";
export const authSlice = createSlice({
  name: 'authentication',
  initialState:{
    token: null,
    loading:false,
    error:null,
    anime_image:'',
    panel:'',
  },
  reducers:{
    
  },
  extraReducers: (builder)=>{
     builder
    //  login user
     .addCase(loginUser.pending, (state)=>{
      state.loading = true;
      state.error = null;
     })
     .addCase(loginUser.fulfilled, (state,action)=>{
      state.loading = false;
      state.token = action.payload;
     })
     .addCase(loginUser.rejected, (state,action)=>{
      state.loading = false;
      state.error = action.payload;
     })

    //  register user
     .addCase(registerUser.pending, (state)=>{
      state.loading = true;
      state.error = null;
     })
     .addCase(registerUser.fulfilled, (state,action)=>{
      state.loading = false;
      state.token = action.payload;
     })
     .addCase(registerUser.rejected, (state,action)=>{
      state.loading = false;
      state.error = action.payload;
     })

    //   image conversion
     .addCase(animeConversion.pending, (state)=>{
      state.loading = true;
      state.error = null;
     })
     .addCase(animeConversion.fulfilled, (state,action)=>{
      state.loading = false;
      state.anime_image = action.payload
      state.anime_image = action.payload;
     })
     .addCase(animeConversion.rejected, (state,action)=>{
      state.loading = false;
      state.error = action.payload;
     })
    
    //  poses generation
    .addCase(posesGeneration.pending,(state)=>{
      state.loading = true;
      state.error = null;
    })
    .addCase(posesGeneration.fulfilled,(state)=>{
      state.loading = false;
      state.error = null
    })
    .addCase(posesGeneration.rejected,(state,action)=>{
      state.loading = false;
      state.error = action.payload;
    })
    
    // generate story
    .addCase(generateStory.pending,(state)=>{
      state.loading = true;
      state.error = null;
    })
    .addCase(generateStory.fulfilled,(state,action)=>{
      state.loading = false;
      state.panel = action.payload
      state.story = action.payload
    })
    .addCase(generateStory.rejected,(state,action)=>{
      state.loading = false;
      state.error = action.payload;
    })
  }
})
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async (credentials, thunkAPI) => {
    try {
      const res = await axios.post('login/', credentials,{
          headers: {
         'Content-Type': 'application/json',
             }
      });
      localStorage.setItem("token", res.data.token);
      toast.success("Logged in Successfully!! ")
      return res.data.token;
    } catch (err) {
      toast.error("User Does not exist")
      return thunkAPI.rejectWithValue(err.response?.data?.error || 'Login failed');
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (credentials, thunkAPI) => {
    try {
      const res = await axios.post('register/', credentials,{
          headers: {
          'Content-Type': 'application/json'
  }
      });
      localStorage.setItem("token", res.data.token);
      toast.success("User registered successfully ")
      return res.data.token;
    } catch (err) {
      toast.error("Account creation error:",err.data)
      return thunkAPI.rejectWithValue(err.response?.data?.error || 'Registration failed');
    }
  }
);

export const animeConversion = createAsyncThunk(
  'animefy/upload',
  async (image, thunkAPI) => {
    const token = localStorage.getItem("token");
    try {
      const res = await axios.post('animefy/', image,{
             params: { token }, 
        });
        toast.success("Character image created successfully!!")
      return res.data.anime_image_url;
    } catch (err) {
      toast.error("Anime conversion failed", err.response?.data);
      return thunkAPI.rejectWithValue(err.response?.data?.error || 'Anime conversion failed');
    }
  }
);

export const posesGeneration = createAsyncThunk(
  'animefy/poses',
  async (_, thunkAPI) => {
    const token = localStorage.getItem("token"); 
    try {
      await axios.post(
        'poses/',
        null,
        {
          params: { token }
        }
      );
      toast.success("Poses Generation Success");
    } catch (err) {
      toast.error("Poses Generation Failed", err.response?.data);
      return thunkAPI.rejectWithValue(err.response?.data?.error || 'Poses Generation failed');
    }
  }
);

export const generateStory = createAsyncThunk(
  'animefy/story',
  async(story,thunkAPI) =>{
      const token = localStorage.getItem("token");
      try{
        const res = await axios.post(
          'story/',
          {story},
          {
            params:{token},
            headers: {
              'Content-Type': 'application/json' // 👈 ensure this if needed
            }
          }
        );
        toast.success("pannel created successfully!!")
        return res.data.panel_image_url;
      } catch(err){
        toast.error("Story generation failed",err.response?.data);
        return thunkAPI.rejectWithValue(err.response?.data?.error || 'Story Generation Failed')
      }
  }
)
export default authSlice.reducer;