"use client"
import { useState,useEffect, useCallback, useRef } from "react";
import { animeConversion, posesGeneration} from "../redux/authSlice";
import { useRouter } from "next/navigation";
import { Toaster } from 'react-hot-toast';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { useDropzone } from "react-dropzone";
import Skeleton from "react-loading-skeleton";
import { useDispatch,useSelector } from "react-redux";
import Cookies from 'js-cookie';
const CharacterCreation = ()=>{
  const [selectedFile, setSelectedFile] = useState(null)
  const dispatch = useDispatch()
   const router = useRouter()
  const animefy = useSelector((state)=> state.authentication)
  // to handle the image upload for  character generation
const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, []);

const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "image/*": []
    }
  });

  const fileInputRef = useRef();

const handleClick = () => {
  fileInputRef.current?.click();
};
useEffect(() => {
  if (!selectedFile) return;
    const form = new FormData();
    form.append("image", selectedFile);
    dispatch(animeConversion(form));
}, [selectedFile]);

  // handle the log out of the user  
const handleLogout = () => {
  Cookies.remove('authToken'); // ❌ Remove the auth token cookie
  window.location.href = "/";  // 🔁 Redirect to home or login
};
const generatePoses = ()=>{
  dispatch(posesGeneration())
}
  return(
    <>
     <Toaster position="top-right" />

    <section className="p-3 lg:p-8 bg-[url(/859013-anime-attack-on-titan-green-live-wallpaper.jpg)] flex justify-center lg:items-center w-full h-screen lg:h-screen md:h-full bg-cover bg-center bg-repeat">
      
      <div className="bg-white/30 md:w-[95%] md:h-[90%] lg:w-[1280px] lg:h-[720px] xl:w-[1980px]  justify-center rounded-2xl flex flex-col items-center p-3">
        
<div className="grid md:grid-cols-1 lg:grid-cols-2 items-center gap-4 w-full h-[20%] p-4">
  
  {/* LEFT SIDE: Title */}
  <div className="flex justify-center lg:justify-start">
    <p className="bg-[#2f9e44] flex justify-center  mt-4 w-[90%] lg:w-[90%] md:w-[50%] px-2 lg:px-6 py-3 rounded-xl text-xl  lg:text-3xl text-white">
      Create Your Own Character
    </p>
  </div>

  {/* RIGHT SIDE: Navigation Buttons */}
  <div className="flex justify-center md:mt-4 lg:justify-end gap-2 lg:gap-4">
    <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={() => router.push("/")}>
      Home
    </button>
    <button className="bg-white text-[#2f9e44] border-[#2f9e44] border-3 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" disabled>
      Character
    </button>
    <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={() => router.push("/generatePanel")}>
      Panel
    </button>
    <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={handleLogout}>
      Logout
    </button>
  </div>

</div>

             <div className="flex flex-col lg:flex-row lg:justify-center items-center h-[100%] w-[100%] md:gap-5">
                             <div className="h-[40%] md:h-[80%] md:w-[60%]  w-[90%] lg:w-[30%] flex mt-6 lg:justify-center items-center flex-col gap:1 lg:gap-3">
                    <div  className="bg-[#2f9e44] w-[80%] md:p-3 gap-4 h-[100%] lg:h-[50%] rounded-xl border-dashed border-4 flex flex-col items-center justify-center">
                      
                      <div {...getRootProps()} className="flex items-center flex-col">
                        <input {...getInputProps()} />
                      <img className="w-[50px] md:w-[40px]" src="/folder.png" />
                      <div className="text-xl text-md mb-2 p-2 text-white/70">{selectedFile ? selectedFile.name : "Drop image"}</div>
                      </div>
                       <input ref={fileInputRef} type="file" onChange={(e) => setSelectedFile(e.target.files[0])} className="hidden"/>                   
                         
                         <button type="button" className="bg-[#40c057] w-25 md:w-20 rounded-lg md:border-3 border-4 text-lg md:text-md text-white" onClick={handleClick}>upload</button>
                   
                    </div>
                    <div className="w-[30%]  h-[25%]">
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
                    {animefy.anime_image && 
                       <div className="flex flex-col justify-center gap-2 lg:w-[20%] w-[60%] md:w-[30%] lg:h-[100%] rounded-2xl">
                         <img className="rounded-2xl w-full h-[70%] object-cover" src={animefy.anime_image} alt="user image" />
                          <button className="bg-[#2f9e44] p-2 border-4 rounded-xl text-lg " onClick={generatePoses}>Confirm your Character</button>
                       </div>
                    }
             </div>
      </div>
    </section>
    </>
  );
}

export default CharacterCreation;