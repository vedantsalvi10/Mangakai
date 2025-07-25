"use client"

import { Provider} from "react-redux";
import store from "./redux/store";
import Landing from "./Home";
export default function Home() {
  return (
    <>
       <Landing />
    </>
  );
}
