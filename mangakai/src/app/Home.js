"use client"
import Cookies from "js-cookie";
import Login from "./components/Login";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Toaster } from "react-hot-toast";
export default function Landing() {
    const router = useRouter()
    const [token,setToken] = useState(null)
    useEffect(() => {
        setToken(Cookies.get('authToken'));
        
    },[])
  return (
    <>
    <Toaster position="top-right"/>
    <section className="p-3 lg:p-8 bg-[url(/859028-anime-snatch-green-background-desktop-wallpaper-1366x768.jpg)] flex justify-center items-center w-full lg:h-screen h-full bg-cover bg-center bg-no-repeat">
     <div className="bg-white/30 md:w-[95%] md:h-[90%] lg:w-[1280px] lg:h-[720px] xl:w-[1980px]  justify-center rounded-2xl flex flex-col items-center">
          <div className=" h-[20%] w-[100%] flex justify-center items-center">
                 <p className=" bg-[#2f9e44] mt-4 p-3 md:p-5  w-[70%] md:w-[50%] flex justify-center rounded-xl text-4xl md:text-5xl">MangaKai</p>
          </div>
           <div className="flex justify-center items-center h-[80%] lg:flex-row flex-col w-[100%] p-5 gap-10 lg:gap-20">

                <div className="border-5 bg-[#40c057] flex justify-center items-center p-5 md:p-3 rounded-xl w-[95%] md:w-[60%] lg:w-[30%] border-dashed h-[80%]"><p>Want to star in your own manga or bring a dream to life as a manga story? With MangaKai, you can! Simply upload a photo of your face and describe how you want your manga panel to look — and we’ll turn it into a personalized manga panel. You can create multiple panels to build a full page, and eventually an entire manga featuring you or any character of your choice. Whether it's an epic fantasy, a slice-of-life moment, or a dream sequence, MangaKai transforms your ideas into manga-style art. Your story, your face, your manga — only with MangaKai.</p></div>
                 {token ? (
                <div className="flex flex-col w-[95%] md:w-[50%] lg:w-[20%] h-[80%] gap-3 text-lg">
                    <img className="rounded-xl  w-[100%] lg:h-[80%] object-cover" src="/trial_image/animeface_00001_.png" alt="user image" />
                    <button className="bg-[#2f9e44] border-5 rounded-xl w-[100%] p-2" onClick={()=>{router.push("/generateCharacter")}}>Get Started</button>
                </div> 
                ):
                (
                  <Login/>
                )}
                  <img className="rounded-2xl w-[95%] md:w-[50%] lg:w-[20%] h-[80%] object-cover" src="/trial_image/anime_pose1.png" alt="user image" />
           </div>
     </div>
      </section>
    </>
  );
}