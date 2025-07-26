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
 <div className="bg-white/30 w-[1980px] h-[700px] rounded-2xl flex flex-col items-center">
         
<div className="grid grid-cols-2 items-center gap-4 w-full h-[15%] p-4">
  
  {/* LEFT SIDE: Title */}
  <div className="flex justify-start">
    <p className="bg-[#2f9e44] px-6 py-3 rounded-xl text-3xl text-white">
      Create Your Manga Panel
    </p>
  </div>

  {/* RIGHT SIDE: Navigation Buttons */}
  <div className="flex justify-end gap-4">
    <button className="bg-[#2f9e44] text-white border-white border-2 px-4 py-2 rounded-lg text-md" onClick={() => router.push("/")}>
      Home
    </button>
    <button className="bg-[#2f9e44] text-white border-white border-2 px-4 py-2 rounded-lg text-md" onClick={() => router.push("/generateCharacter")}>
      Character
    </button>
    <button className="bg-white text-[#2f9e44] border-[#2f9e44] border-2 px-4 py-2 rounded-lg text-md" disabled onClick={() => router.push("/generatePanel")}>
      Panel
    </button>
    <button className="bg-[#2f9e44] text-white border-white border-2 px-4 py-2 rounded-lg text-md" onClick={handleLogout}>
      Logout
    </button>
  </div>

</div>
        {/* <div className="flex w-[100%] h-[20%] justify-center">
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
        </div> */}
        <div className="flex justify-center items-center h-[100%] w-[100%] gap-5">
                    <div className="h-[100%] w-[30%] flex justify-center items-center flex-col gap-3">
                    <div className="bg-[#2f9e44] w-full gap-4 h-[50%] rounded-xl border-dashed border-4 flex flex-col items-center justify-center">
                           <textarea className=" w-[100%] h-[80%] placeholder:p-2 text-lg text-[#ebfbee]  placeholder-[#b2f2bb] resize-none overflow-auto p-3 outline-none" value={story} onChange={(e)=>{setStory(e.target.value)}} type="text"placeholder="Write your panel story over here..." />
                           <div className="flex w-[full] justify-center items-center mb-3">
                                 <button className="bg-[#40c057] text-white w-25 rounded-lg border-4 text-lg" onClick={handlePanelGeneration}>Generate</button> 
                            </div>
                    </div>
                     <div className="w-[30%] h-[25%]">
                     {animefy.loading && 
                     <div className="w-full h-full">
                         <DotLottieReact
                   src="https://lottie.host/ae57be7c-b080-49bf-bdcf-a292dd7d9dac/F275oCskAs.lottie"
                   loop
                   autoplay
                 />
                 </div>
              
                     }
                       </div>
          </div>
                    {animefy.panel &&
                    <div className="flex flex-col gap-5 w-[300px]  h-[500px] rounded-2xl">
                         <img className=" w-full h-[90%] object-cover" src={animefy.panel} alt="user image" />   
                          <button className="bg-[#2f9e44] p-2 border-4 rounded-xl text-lg " onClick={downloadImage}>Download</button>
                    </div>
                  } 
        </div>
    </div>
  </section>
  </>);

}
export default PanelGeneration;