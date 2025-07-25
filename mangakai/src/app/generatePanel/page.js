"use client"
import { useState,useEffect } from "react";
import React from 'react';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { Toaster } from 'react-hot-toast';
import { useRouter } from "next/navigation";
import { generateStory} from "../redux/authSlice";
import { useDispatch, useSelector  } from "react-redux";
const PanelGeneration = ()=>{
const [story,setStory] = useState()
const dispatch = useDispatch()
const router = useRouter()
const animefy = useSelector((state)=> state.authentication)
const handlePanelGeneration = () =>{
  dispatch(generateStory( story ));
}
// download image
const downloadImage = async () => {
  try {
    const response = await fetch(animefy.panel, { mode: 'cors' });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'manga_panel.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up the blob URL
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Download failed:", error);
  }
};
  // handle the log out of the user  
  const handleLogout = () => {
  localStorage.removeItem("token");
  // redirect to login or homepage
  window.location.href = "/";
  };

return(
<>
 <Toaster position="top-right" />
<section className="p-8 bg-[url(/859013-anime-attack-on-titan-green-live-wallpaper.jpg)] flex justify-center items-center w-full h-screen bg-cover bg-center bg-no-repeat" >
 <div className="bg-white/20 w-[1980px] h-[700px] rounded-2xl p-10 flex flex-col items-center">
        <div className="flex w-[100%] h-[20%] justify-center">
                 {animefy.loading && 
        <div>
            <DotLottieReact
      src="https://lottie.host/19cde61b-f468-4f22-9c4f-d11abb5488b1/zo0f6WbsCp.lottie"
      loop
      autoplay
    />
    </div>}
        <div className=" h-[100%] w-[80%] flex justify-center items-center">
                <p className=" bg-[#2f9e44] p-5 w-[70%] flex justify-center rounded-xl text-5xl">Generate Manga Panael</p>
        </div>
 
        <div className="w-[10%] h-full flex items-center justify-center">
               <button className=" bg-[#2f9e44] p-2 pl-4 pr-4  text-white border-white border-4 rounded-xl text-lg " onClick={handleLogout}>logout</button>
             </div>  
        </div>
        <div className="flex justify-center h-[90%] w-[100%]  p-7 gap-20">
                    <div className="h-[90%] w-[50%] items-center flex flex-col  gap-10">
                     <div className="flex w-full gap-5 justify-center">
                    <button  className="bg-[#2f9e44] text-white border-white [30%] p-2 pl-3 pr-3 border-4 rounded-xl text-lg "  onClick={()=>{router.push("/")}}>Home</button>
                    <button  className="bg-[#2f9e44] text-white border-white w-[40%] p-2 border-4 rounded-xl text-lg " onClick={()=>{router.push("/generateCharacter")}}>Character Generator</button>
                    <button  className="bg-[#40c057]/70 text-white border-white/70  w-[30%] p-2 border-4 rounded-xl text-lg "  onClick={()=>{router.push("/generatePanel")}}>Panel Generator</button>
                    </div>
                    <div className="border-5 bg-[#2f9e44] w-[90%] rounded-xl border-dashed h-[90%]">
                           <textarea className=" w-[100%] h-[80%] placeholder:p-2 text-lg text-[#ebfbee]  placeholder-[#b2f2bb] resize-none overflow-auto p-3 outline-none" value={story} onChange={(e)=>{setStory(e.target.value)}} type="text"placeholder="Write your panel story over here..." />
                           <div className="flex w-[full] justify-center items-center mb-3">
                                 <button className="bg-[#40c057] text-white w-25 rounded-lg border-4 text-lg" onClick={handlePanelGeneration}>Generate</button> 
                            </div>
                    </div>
          </div>
                    {animefy.panel &&
                    <div className="flex flex-col gap-5 w-[300px]  h-[500px] rounded-2xl">
                         <img className=" w-full h-[90%] object-cover" src={animefy.panel} alt="user image" />   
                          <button className="bg-[#2f9e44] text-white p-4 border-5 rounded-xl text-xl " onClick={downloadImage}>Download</button>
                    </div>
                  } 
        </div>
    </div>
  </section>
  </>);

}
export default PanelGeneration;