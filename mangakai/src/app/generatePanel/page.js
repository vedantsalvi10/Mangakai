"use client"
import { useState,useEffect } from "react";
import React from 'react';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { Toaster } from 'react-hot-toast';
import { useRouter } from "next/navigation";
import { generateStory} from "../redux/authSlice";
import { useDispatch, useSelector  } from "react-redux";
import Cookies from 'js-cookie';
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
const handleLogout = () => {
  Cookies.remove('authToken'); // ❌ Remove the auth token cookie
  window.location.href = "/";  // 🔁 Redirect to home or login
};


return(
<>
 <Toaster position="top-right" />
<section className="p-3 lg:p-8 bg-[url(/859013-anime-attack-on-titan-green-live-wallpaper.jpg)] flex justify-center lg:items-center w-full h-screen lg:h-screen md:h-full bg-cover bg-center bg-repeat" >
 <div className="bg-white/30 md:w-[95%] md:h-[90%] lg:w-[1280px] lg:h-[720px] xl:w-[1980px]  justify-center rounded-2xl flex flex-col items-center p-3">
         
<div className="grid md:grid-cols-1 lg:grid-cols-2 items-center gap-4 w-full h-[20%] p-4">
  
  {/* LEFT SIDE: Title */}
  <div className="flex justify-center lg:justify-start">
    <p className="bg-[#2f9e44] flex justify-center  mt-4  w-[80%] lg:w-[80%] md:w-[50%] px-2 lg:px-6 py-3 rounded-xl text-xl  lg:text-3xl text-white">
      Create Your Manga Panel
    </p>
  </div>

  {/* RIGHT SIDE: Navigation Buttons */}
  <div className="flex justify-center md:mt-4 lg:justify-end gap-2 lg:gap-4">
    <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={() => router.push("/")}>
      Home
    </button>
    <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={() => router.push("/generateCharacter")}>
      Character
    </button>
    <button className="bg-white text-[#2f9e44] border-[#2f9e44] border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" disabled onClick={() => router.push("/generatePanel")}>
      Panel
    </button>
    <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={handleLogout}>
      Logout
    </button>
  </div>

</div>
        <div className="flex flex-col lg:flex-row lg:justify-center items-center h-[100%] w-[100%] md:gap-5">
                    <div className="h-[40%] md:h-[80%] md:w-[60%]  w-[90%] lg:w-[30%] flex mt-6 lg:justify-center items-center flex-col gap:1 lg:gap-3">
                    <div className="bg-[#2f9e44] w-full gap-4 h-[75%] lg:h-[50%] rounded-xl border-dashed border-4 flex flex-col items-center justify-center">
                           <textarea className=" w-[100%] h-[80%] md:text-md text-lg text-[#ebfbee]  placeholder-[#b2f2bb] resize-none overflow-auto p-3 outline-none" value={story} onChange={(e)=>{setStory(e.target.value)}} type="text"placeholder="Write your panel story over here..." />
                           <div className="flex w-[full] justify-center items-center mb-3">
                                 <button className="bg-[#40c057] text-white w-25 rounded-lg border-4 text-lg" onClick={handlePanelGeneration}>Generate</button> 
                            </div>
                    </div>
                     <div className="w-[25%] lg:w-[30%] h-[25%] lg:h-[25%]">
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
                    <div className="flex flex-col gap-3 lg:gap-5 w-[70%] md:w-[50%] md:h-[40%] lg:w-[300px] h-[80%] lg:h-[500px] rounded-2xl">
                         <img className=" w-full h-[90%] object-cover" src={animefy.panel} alt="user image" />   
                          <button className="bg-[#2f9e44] mb-3 p-2 border-4 rounded-xl text-md lg:text-lg " onClick={downloadImage}>Download</button>
                    </div>
                  } 
        </div>
    </div>
  </section>
  </>);

}
export default PanelGeneration;