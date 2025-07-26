"use client"
import { useState,useEffect, useCallback, useRef } from "react";
import { animeConversion, posesGeneration} from "../redux/authSlice";
import { useRouter } from "next/navigation";
import { Toaster } from 'react-hot-toast';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { useDropzone } from "react-dropzone";
import Skeleton from "react-loading-skeleton";
import { useDispatch,useSelector } from "react-redux";

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
  localStorage.removeItem("token");
  // redirect to login or homepage
  window.location.href = "/";
  };
const generatePoses = ()=>{
  dispatch(posesGeneration())
}
  return(
    <>
     <Toaster position="top-right" />

    <section className="p-8 bg-[url(/859013-anime-attack-on-titan-green-live-wallpaper.jpg)] flex justify-center items-center w-full h-screen bg-cover bg-center bg-no-repeat">
      
      <div className="bg-white/30 w-[1980px] h-[700px] rounded-2xl flex flex-col items-center">
        
<div className="grid grid-cols-2 items-center gap-4 w-full h-[15%] p-4">
  
  {/* LEFT SIDE: Title */}
  <div className="flex justify-start">
    <p className="bg-[#2f9e44] px-6 py-3 rounded-xl text-3xl text-white">
      Create Your Own Character
    </p>
  </div>

  {/* RIGHT SIDE: Navigation Buttons */}
  <div className="flex justify-end gap-4">
    <button className="bg-[#2f9e44] text-white border-white border-2 px-4 py-2 rounded-lg text-md" onClick={() => router.push("/")}>
      Home
    </button>
    <button className="bg-white text-[#2f9e44] border-[#2f9e44] border-3 px-4 py-2 rounded-lg text-md" disabled>
      Character
    </button>
    <button className="bg-[#2f9e44] text-white border-white border-2 px-4 py-2 rounded-lg text-md" onClick={() => router.push("/generatePanel")}>
      Panel
    </button>
    <button className="bg-[#2f9e44] text-white border-white border-2 px-4 py-2 rounded-lg text-md" onClick={handleLogout}>
      Logout
    </button>
  </div>

</div>

             <div className="flex justify-center items-center h-[100%] w-[100%] gap-5">
                             <div className="h-[100%] w-[30%] flex justify-center items-center flex-col gap-3">
                    <div  className="bg-[#2f9e44] w-full gap-4 h-[50%] rounded-xl border-dashed border-4 flex flex-col items-center justify-center">
                      
                      <div {...getRootProps()} className="flex items-center flex-col">
                        <input {...getInputProps()} />
                      <img className="w-[50px]" src="/folder.png" />
                      <div className="text-xl mb-2 text-white/70">{selectedFile ? selectedFile.name : "Drop image"}</div>
                      </div>
                       <input ref={fileInputRef} type="file" onChange={(e) => setSelectedFile(e.target.files[0])} className="hidden"/>                   
                         
                         <button type="button" className="bg-[#40c057] w-25 rounded-lg border-4 text-lg text-white" onClick={handleClick}>upload</button>
                   
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
                    {animefy.anime_image && 
                       <div className="flex flex-col justify-center gap-2 w-[20%] h-[100%] rounded-2xl">
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